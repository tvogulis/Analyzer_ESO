from bs4 import BeautifulSoup
import requests
import datetime
import pandas as pd


def date_range(start_date, end_date):
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    while start_date <= end_date:
        yield start_date.strftime('%Y-%m-%d')
        start_date += datetime.timedelta(days=1)

while True:
    try:
        start_date = input("Enter start date - (i.e. 2024-01-24) : ")
        data = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        break
    except ValueError:
        print("Date format must be as in example ")

while True:
    try:
        end_date = input("Enter end date - (i.e. 2024-01-24) : ")
        data = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        break
    except ValueError:
        print("Date format must be as in example ")

# start_date = ('2024-04-30')
# end_date = ('2024-05-01')

main_df = pd.DataFrame(columns=['Date', 'Nord Pool Price'])
count = 0

for date in date_range(start_date, end_date):
    source = requests.get(
        f'https://www.litgrid.eu/index.php/sistemos-duomenys/elektros-energijos-kainos/86?lines=150&filter%5Bfrom%5D={date}&filter%5Bto%5D={date}&submit=Vykdyti').text
    soup = BeautifulSoup(source, 'html.parser')
    main_block = soup.find('tbody')

    date_price_lists = []
    for tr in main_block.find_all('tr'):
        date_price_raw = tr.find_all('td')
        date_price_single = []
        for element in date_price_raw:
            date_price_single.append(element.text.strip())
        date_price_lists.append(date_price_single)

    nord_pool_dates = []
    nord_pool_prices = []
    for x in date_price_lists:
        nord_pool_dates.append(x[0])
        nord_pool_prices.append(x[1])
    df = pd.DataFrame({'Date': nord_pool_dates, 'Nord Pool Price': nord_pool_prices})

    count += 1
    print(count)

    for index, row in df.iterrows():
        if row['Date'] not in main_df['Date'].values:
            main_df = main_df._append(row, ignore_index=True)

main_df.to_csv(f'Nord_Pool {start_date}_{end_date}.csv', index=False)
print(f'Nord Pool prices collection finished, file name : "Nord_Pool {start_date}_{end_date}.csv"')
