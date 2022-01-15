import backtesting_support
import eikon as ek

# Set Eikon App Key
ek.set_app_key('DEFAULT_CODE_BOOK_APP_KEY')

# Eikon Index RIC
index_ric = '.SPX'
# Start date
start_date = '20160101'
# Number of best asset based on fundamental data to incude in our portfolio
num_assets = 10
# Set total number of backtestings
num_backtesting = 100

# Create class
backtesting = backtesting_support.BackTesting(index_ric, start_date, num_assets)

# Run backtesting
all_returns_df, all_backtesting_results_list = backtesting.run_multiple_backtesting(num_backtesting, 
                                                                                    years = 3)
