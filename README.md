# backtesting
On this repository you can find a backtesting code for a buy and hold strategy.  

# What file you should run?
To run the code run file backtesting.py. 
backtesting_support.py file is the module used. Make sure it is installed in your venv

# Previous tasks?
The code runs a back testing based on the analysis performed based on the codes that you can find on the data_analysis repository. 

# What the code does? 
The code will use the start_date passed to calculated 100 bactesting based on different starting dates within the interval start_date + 6 months 
Investment period can be changed when running function backtesting.run_multiple_backtesting(num_backtesting, years = 3). Just change years parameter.  
Final results will be saved and several box and scatter graphs and will be printed to illustrate the results.  
You can find some examples bellow:

![box](https://user-images.githubusercontent.com/69301150/149621881-e7ca1d57-440c-4c7e-952e-ecb7c4e0e928.png)
![scatter_no_alpha](https://user-images.githubusercontent.com/69301150/149621884-e95ee277-833c-4073-ba8e-f4e7b44e1f6f.png)
![scatter](https://user-images.githubusercontent.com/69301150/149621885-0258c676-31c2-4cf5-8225-06ad00a8ed40.png)
