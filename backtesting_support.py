import pandas as pd
import eikon as ek
import numpy as np
from tqdm.notebook import tqdm
import datetime
from random import randrange
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import pickle

class BackTesting:
    def __init__(self, index_ric, start_date, num_assets):
        '''
        Args:
            index_ric: Reuters index RIC 
        Returns:
            None
        '''
        self.index_ric = index_ric
        self.start_date = start_date
        self.num_assets = num_assets
        self.base_path = 'backtesting/'
        self.selected_assets = pd.DataFrame()
        self.asset_performance = pd.DataFrame()
        self.index_performance = pd.DataFrame()
        self.ric_list = []
        self.backtesting_start_date = None
        self.backtesting_end_date =  None

    def get_index(self, fields_list, start_date):
        '''
        Downloads equity index consituents on a specific date

        Args:
            index_ric: Eikon Index RIC
            feilds_list: list with fields code to be downloaded
            start_date: date on which index constituents will be downloaded
        Returns:
            index_df: df with Constituent RIC and Names
        '''
        # Create DataFrame for our index constituents
        index_df = pd.DataFrame()
        # Create object where we will save the number of iterations
        count = 0
        # While DF lenght is smaller than one (Eikon Api answer is empty), we'll send another request
        while len(index_df) <= 1:
            # Fields list
            fields_list = ['TR.IndexConstituentRIC', 'TR.ETPConstituentName']
            # Get data
            index_df = ek.get_data(instruments = self.index_ric, 
                                   fields = fields_list,
                                   parameters = {'SDate': self.start_date})[0]
            if count == 2:
                print('We could not download equity index constituents for date', start_date)
                break
            count += 1
        # Save answer into multiple formats
        self.save_df(df = index_df, file_name = self.index_ric[1:], 
                                                intermedate_1='data_downloaded/', 
                                                intermedate_2='final_data/')
        
    def select_assets(self, results_df, num_assets = 10):
        '''
        Selects assets of our results DataFrame
        
        Args:
            results_df: DF with algorithm analysis results
            num_assets: number of best assets we want to use. Default 10.
        Returns:
            None
        '''
        self.selected_assets = results_df.sort_values(by = 'score', ascending = False).iloc[:num_assets,-2:]
        self.ric_list = self.selected_assets.index.values.tolist()
        
    def get_price_close(self, ric_list, date):
        '''
        Downloads close price for specific RIC code and date
        
        Args:
            ric_list: list with the asset ric codes
            date: price close date to be downloaded
        Returns:
            df: df with price close per asset RIC
            err: error answer from Eikon API
        '''
        # Request data
        df, err = ek.get_data(instruments = ric_list, 
                                  fields = 'TR.PriceClose',
                                  parameters = {'SDate': date})
        # Change column name to the specific date
        return df, err
    
    def change_column_name(self, df, column_name):
        '''
        Changes column name for the specifc df received from Eikon get_data request. 

        Args:
            df: df with financial data
            column_name: new column name
        Returns:
            df: df with new column name
        '''
        df.columns = ['Instrument', column_name]
        return df

    def get_asset_performance(self, start_date, end_date, ric_list):
        '''
        Gets start and end date prices and calculates percentage and log returns. 
        
        Args:
            start_date: starting date of the backtesting
            end_date: ending date of the backtesting
            ric_list: asset ric codes. Default: best performing assets according to
                      our algorithm analysis.
        Returns:
            None
        '''
        # Eikon API cometimes returns errors for correct request. 
        # We build our requesto to avoid this problem
        count = 0
        err = 'Error Object'
        while err != None:
            # Get start date close prices
            df, err = self.get_price_close(ric_list, date = start_date)
            # In case we receive an error, we want to know
            if count != 0:
                print('Error from Eikon API for', start_date, 'and', ric_list, 'request number', count, 'try again')
            count += 1
        # Change column name to the specific date
        df = self.change_column_name(df, column_name=start_date)
        # Eikon API cometimes returns errors for correct request. 
        # We build our requesto to avoid this problem
        count = 0
        err = 'Error Object'
        while err != None:
            # Get end date close prices
            df_end_date, err = self.get_price_close(ric_list, date = end_date)
            if count !=0:
                # In case we receive an error, we want to know
                print('Error from Eikon API for', end_date, 'and', ric_list, 'request number', count, 'try again')
            count += 1
        # Change column name to the specific date and select last column
        df[end_date] = self.change_column_name(df_end_date, column_name=end_date).iloc[:,-1]
        # Calculate percentage return
        df['return'] = ((df.iloc[:,2] / df.iloc[:,1]) - 1) * 100
        # Calculare log return 
        df['log_return'] = np.log(df.iloc[:,2]/df.iloc[:,1]) * 100
        return df
    
    def get_equally_weighted_portfolio(self):
        '''
        Creates a allocation dictionary following a equally weighted portfolio
        strategy among the assets that have been selected
        
        Args:
            None
        Returns:
            allocation_dict: allocation dictionary with weight per asset
        '''
        # Create allocation dictionary
        allocation_dict = {}
        # Calculate equally asset weight
        equally_weighted = 1/len(self.asset_performance)
        for asset in self.asset_performance.loc[:,'Instrument']:
            allocation_dict[asset] = equally_weighted
        return allocation_dict
    
    def calculate_portfolio_return(self, allocation_dict):
        '''
         Calculates portfolio return according to an allocation dictionary
        
        Args:
            allocation_dict: allocation dictionary with weight per asset
        Returns:
            portfolio_return: return of the portfolio
        '''
        # Create portfolio_return variable
        portfolio_return = 0
        # Iterate among dict items
        for asset, weight in list(allocation_dict.items()):
            # Create bolean mask
            boolean_mask = self.asset_performance.loc[:,'Instrument'] == asset
            # Get reutrn for the specific asset
            profit = self.asset_performance.loc[boolean_mask,'return'].values[0]
            # Calculate protfolio return
            portfolio_return = portfolio_return + (profit/100) * weight
        # Multiply return by 100
        portfolio_return = portfolio_return * 100
        return portfolio_return
        
    def get_portfolio_return(self, equally_weighted = True, allocation_dict = None):
        '''
        Checks portfolio distribution and returns portfolio return
        
        Args:
            equally_weighted: wether we want to follow an equally weighted strategy
            allocation_dict: if equally_weighted == False, an allocation list must be passed. 
                             Example: {'MSFT.OQ': 0.7, 'MNST.OQ':0.3}
        Returns:
            portfolio_return: return of the portfolio
        '''
        # Check if we are running for an allocation dictionary
        if (equally_weighted == True) and (allocation_dict == None):
            # Get equally weighted portfolio allocation dictionaery
            allocation_dict = self.get_equally_weighted_portfolio()
            # Calculate portfolio return
            portfolio_return = self.calculate_portfolio_return(allocation_dict)
            return portfolio_return
        elif (equally_weighted == False) and (allocation_dict != None):
            # Calculate portfolio return
            portfolio_return = self.calculate_portfolio_return(allocation_dict)
            return portfolio_return
        elif (equally_weighted == False) and (allocation_dict == None):
            print(f'Error: if equally_weighted == False, an allocation_dict must be passed')
        elif (equally_weighted == True) and (allocation_dict != None):
            print(f'Error: if equally_weighted == True, no allocation_dict must be passed')
    
    def get_backtestign_start_date(self, date_string, month_interval = 6):
        '''
        Finds a random backtesting start date between the date passed in in string
        format and the number of months passed after that date.
        
        Args:
            date_string: date in string formar yyyymmdd
            month_interval: number of month to consider after date_string
                            within which we generate a random date 
        '''
        # Get start date in datetime format
        start_date_datetime = self.get_datetime_format(date_string)
        # Get upper date limit
        upper_date_limit = start_date_datetime + relativedelta(months = month_interval)
        # Get interval of days
        days_between_dates = (upper_date_limit - start_date_datetime).days
        # Get random number
        random_number_of_days = randrange(days_between_dates)
        # Get backtesting start date
        self.backtesting_start_date = start_date_datetime + datetime.timedelta(days=random_number_of_days)
        
    
    def get_backtesting_end_date(self, date, years):
        '''
        Gets backtesting end date
        Args:
            date: start date in datetime format
            years: interval in years
        Returns:
            backtesting_end_date: backtesting end date in datetime format
        '''
        self.backtesting_end_date = date + relativedelta(years=years)
    
    def get_datetime_format(self, date_string):
        '''
        Transforms a date receive in string format to datetime format
        
        Args:
            date_string: date in string formar yyyymmdd
        Returns:
            date: date in datetime format
        
        '''
        year = int(date_string[0:4])
        month = int(date_string[4:6])
        day = int(date_string[6:8])
        date = datetime.date(year, month, day)
        return date
    
    def get_date_string_format(self, date_datetime):
        '''
        Transforms a date receive in datetime format to string format yymmdd
        
        Args:
            date_datetime: date in datetime format
        Returns:
            date_string: date in string format yymmdd
        '''
        date_string = date_datetime.strftime('%Y%m%d')
        return date_string
    
    def resume_backtesting_results(self, years):
        '''
        Saves resutls into a dictionary
        
        Args:
            years: investment period
        Returns:
            None
        '''
        # Save data
        backtesting_results_dict = {}
        backtesting_results_dict['num_assets'] = self.num_assets
        backtesting_results_dict['selected_assets'] = self.selected_assets
        backtesting_results_dict['ric_list'] = self.ric_list
        backtesting_results_dict['start_date'] = self.backtesting_start_date
        backtesting_results_dict['end_date'] = self.backtesting_end_date
        backtesting_results_dict['investment_period'] = years
        backtesting_results_dict['asset_performance'] = self.asset_performance
        backtesting_results_dict['index_performance'] = self.index_performance
        backtesting_results_dict['portfolio_return'] = self.portfolio_return
        return backtesting_results_dict
    
    def run_back_testing(self, years):
        '''
        Runs backtesting 
        
        Args:
            years: investment period
        Returns:
            returns_df: DF with portfolio and index return
        '''
        # Read results file
        file_name = 'results_raw'
        results_df = self.read_file(file_name)
        # Select best assets
        self.select_assets(results_df, self.num_assets)
        # Get backtesting start date
        self.get_backtestign_start_date(self.start_date)
        # Get backtesing end date
        self.get_backtesting_end_date(self.backtesting_start_date, years)
        # Get string format
        backtesting_start_date_string = self.get_date_string_format(self.backtesting_start_date)
        backtesting_end_date_string = self.get_date_string_format(self.backtesting_end_date)
        # Get performance of every asset between the generated dates
        self.asset_performance = self.get_asset_performance(backtesting_start_date_string, 
                                                            backtesting_end_date_string, 
                                                            self.ric_list)
        # Get index performance
        self.index_performance = self.get_asset_performance(backtesting_start_date_string, 
                                                            backtesting_end_date_string, 
                                                            self.index_ric)
        # Calculate performance return
        self.portfolio_return = self.get_portfolio_return(equally_weighted = True, allocation_dict = None)
        # Resum results in a dictionary
        backtesting_results_dict = self.resume_backtesting_results(years)
        # Save portfolio and index returns into DataFrame
        index_performance = self.index_performance.iloc[0,3]
        portfolio_return = self.portfolio_return
        returns_df = pd.DataFrame([[index_performance,portfolio_return]], 
                                       columns=['index_performance', 'portfolio_return'])
        return returns_df, backtesting_results_dict
    
    def run_multiple_backtesting(self, num_backtesting, years):
        '''
        Runs multiple backtesting 
        
        Args:
            num_backtesting: number of backtestings
            years : investment period
        Returns:
            returns_df: DF with portfolio and index returns of all backtestings
            all_backtesting_results_list : list with dictionaries that contain every backtesting results
        '''
        all_backtesting_results_list = []
        print('Running backtesting')
        # Start running the backtestings
        for backtesting in tqdm(range(0,num_backtesting,1)):
            # First itereation we create list and DF
            if backtesting == 0:
                # Receive data
                returns_df, backtesting_results_dict = self.run_back_testing(years)
                # Save data
                all_returns_df = returns_df
                all_backtesting_results_list = [backtesting_results_dict]
            else:
                # For the following iter, we append results to existing DF and list
                returns_df, backtesting_results_dict = self.run_back_testing(years)
                # 
                all_returns_df = all_returns_df.append(returns_df)
                all_backtesting_results_list.append(backtesting_results_dict)
        # Reset index
        all_returns_df = all_returns_df.reset_index(drop = True)
        # Save data
        self.save_df(all_returns_df, file_name='all_returns', intermedate_1='results/')
        self.save_list(all_backtesting_results_list, 'results_list', 'results/')
        # Draw and save graphs
        self.save_graphs(all_returns_df)
        return all_returns_df, all_backtesting_results_list

    def save_graphs(self, all_returns_df):
        '''
        Draw and saves box and scatter plot graphs
        
        Args:
            all_returns_df: DF with the data to be drawn
        Returns:
            None
        '''
        # Calculate alpha
        all_returns_df['alpha'] = all_returns_df['portfolio_return'] - all_returns_df['index_performance']
        # Plot results scatter graph
        all_returns_df.plot.scatter(x = 'index_performance', 
                                    y = 'portfolio_return', 
                                    c='alpha', 
                                    cmap="viridis",
                                    s=20)
        plt.savefig(self.base_path + self.index_ric[1:] + '/results/' + 'scatter.png', dpi = 200)
        # Second grapgh
        all_returns_df.plot.scatter(x = 'index_performance', 
                                    y = 'portfolio_return', 
                                    s=20)
        plt.savefig(self.base_path + self.index_ric[1:] + '/results/' + 'scatter_no_alpha.png', dpi = 200)
        # Plot box grapgh
        all_returns_df.plot.box()
        plt.savefig(self.base_path + self.index_ric[1:] + '/results/' + 'box.png', dpi = 200)
    
    def save_list(self, list_to_pickle, file_name, intermedate_1 = '', intermedate_2 = ''):
        '''
        Save list to pickle
        
        Args:
            list_to_pickle: list to be saveb to pickle
            file_name: name of the file saved
            intermedate_1: folder name
            intermedate_2: scond folder name
        Returns:
            None
        '''
        # Build path file
        path_file = self.base_path + self.index_ric[1:] + '/' + intermedate_1 + intermedate_2 
        # Save file
        open_file = open(path_file + file_name, "wb")
        pickle.dump(list_to_pickle, open_file)
        open_file.close()
    
    def save_df(self, df, file_name, intermedate_1 = '', intermedate_2 = ''):
        '''
        Save DF to different formats
        
        Args:
            df: DataFrame to be saved
        Returns:
            None
        '''
        # build path field
        path_file = self.base_path + self.index_ric[1:] + '/' + intermedate_1 + intermedate_2
        # Save DF into multiple formats
        df.to_pickle(path_file + 'pkl/' + file_name + '.pkl')
        df.to_csv(path_file + 'csv/' + file_name + '.csv')
        df.to_excel(path_file + 'xlsx/' + file_name + '.xlsx')
        
    def read_file(self, file_name):
        '''
        Reads file name
        
        Args: 
            file_name: name of the file to be opened
        Returns:
            df: DF
        '''
        # Create path
        path_file = self.base_path + self.index_ric[1:] + '/' + 'results/pkl/raw/' + file_name
        # Reutrns DF
        df = pd.read_pickle(path_file + '.pkl')
        return df

######### End Backtesting ########

def read_list_from_pickle(path):
    '''
    Reads list from pickle
        
    Args:
        path: file path
    Returns:
        mynewlist: opened list
    '''
    with open(path, 'rb') as f:
        mynewlist = pickle.load(f)
        return mynewlist
