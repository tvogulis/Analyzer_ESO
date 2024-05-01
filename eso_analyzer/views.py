import datetime
import time
import pandas as pd

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.views.generic import ListView, DetailView
from pandas._libs.tslibs.parsing import DateParseError
from pandas.errors import EmptyDataError

from .models import CsvFileUpload, PandasStorage, Calculations, MainPrices, IndividualPrices, NordPoolData
from .forms import CsvFileUploadForm, IndividualPricesForm, NordPoolUploadForm, MainPricesForm


def index(request):
    count_users = User.objects.count()
    num_visits = request.session.get('num_visits', 1)
    request.session['num_visits'] = num_visits + 1
    context = {
        'users_total': count_users,
        'num_visits': num_visits,
    }
    return render(request, 'index.html', context)


@csrf_protect
def register(request):
    """Registration form"""

    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        if password == password2:
            if User.objects.filter(username=username).exists():
                messages.error(request, f'User "{username}" exists!')
                return redirect('register')
            else:
                if User.objects.filter(email=email).exists():
                    messages.error(request, f'User with emai -  "{email}" exists!')
                    return redirect('register')
                else:
                    User.objects.create_user(username=username, email=email, password=password)
                    messages.info(request, f'User "{username}" registered!')
                    return redirect('index')
        else:
            messages.error(request, 'Paswords do not match!')
            return redirect('register')
    return render(request, 'register.html')


@login_required
def upload_csv_document(request):
    """ ESO csv report upload, CSV to Pandas dataframe, drop some columns, correct date format,
     calculations + storage to DB, RAW data storage to DB, copy default prices"""

    start_time = time.time()

    if request.method == 'POST':
        form = CsvFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.user = request.user

            # CSV to Pandas, correct date format,
            try:
                df = pd.read_csv(document.csv_file, sep=';')
                df['Data, valanda'] = pd.to_datetime(df['Data, valanda'], utc=True)
                df['Data, valanda'] = df['Data, valanda'].dt.tz_convert('Europe/Vilnius')
                df['Data, valanda'] = df['Data, valanda'].dt.tz_localize(None)
                df['Data, valanda'] = df['Data, valanda'].dt.tz_localize('UTC')

                # Calculations by months and energy type
                monthly_group = df.groupby([df['Data, valanda'].dt.year,
                                            df['Data, valanda'].dt.month,
                                            df['Energijos tipas']])
                monthly_sum = monthly_group['Kiekis, kWh'].sum().unstack()

                # Store calc to DB
                sum_to_storage = []
                for date_index, row in monthly_sum.iterrows():
                    year = date_index[0]
                    month = date_index[1]
                    date = datetime.date(year, month, 1)
                    sum_to_storage.append(Calculations(
                        csv_file=document,
                        date=date,
                        sum_p_plus=round(row['P+'], 0),
                        sum_p_minus=round(row['P-'], 0),
                        sum_q_plus=round(row['Q+'], 0),
                        sum_q_minus=round(row['Q-'], 0)
                    ))
                document.save()
                Calculations.objects.bulk_create(sum_to_storage)
                print(f"--- {time.time() - start_time} seconds CALC storage---")

                # store RAW data to DB
                df_to_storage = []
                for _, row in df.iterrows():
                    df_to_storage.append(PandasStorage(
                        csv_file=document,
                        power_kw=row['Leistinoji galia, kW'],
                        date_time=row['Data, valanda'],
                        energy_type=row['Energijos tipas'],
                        consumption_kwh=row['Kiekis, kWh']
                    ))
                PandasStorage.objects.bulk_create(df_to_storage)

                print(f"--- {time.time() - start_time} seconds RAW data storage---")

            except (EmptyDataError, DateParseError) as error:
                messages.error(request, f'Your report is broken or something wrong with it! File was not uploaded')
                messages.error(request, f'Error: ({error})')
                messages.info(request, f'If you sure your report is ok (direct from ESO) sent it to admin to check! ')
                return redirect('upload')

            # Copy default prices
            try:
                copy_prices = MainPrices.objects.latest('date')
                set_prices = IndividualPrices(
                    csv_file=document,
                    date=copy_prices.date,
                    price_kwh=copy_prices.price_kwh,
                    price_kw=copy_prices.price_kw,
                    price_percent=copy_prices.price_percent,
                    supplier_price=copy_prices.supplier_price,
                    supplier_price_day=copy_prices.supplier_price_day,
                    supplier_price_night=copy_prices.supplier_price_night,
                    sell_price=copy_prices.sell_price,
                    plant_power=copy_prices.plant_power,
                )
                set_prices.save()
                messages.success(request, f"File upload and write to models success! Time spent "
                                          f"{round(time.time() - start_time, 4)} seconds")
                print(f"--- {time.time() - start_time} seconds CSV UPLOAD time total---")

            except ObjectDoesNotExist:
                set_prices = IndividualPrices(
                    csv_file=document,
                    date=datetime.datetime.now(),
                    price_kwh=0,
                    price_kw=0,
                    price_percent=0,
                    supplier_price=0,
                    supplier_price_day=0,
                    supplier_price_night=0,
                    sell_price=0,
                    plant_power=0,
                )
                set_prices.save()
                messages.error(request, f'Ask ADMIN to fill "MainPrices" model! ')
                messages.info(request, f'You will be able fill yourself but please call ADMIN !!! Time spent {round(time.time() - start_time, 4)} seconds')

            return redirect('upload')

    else:
        form = CsvFileUploadForm()

    context = {'form': form}
    return render(request, 'upload_csv.html', context)


class FilesListView(LoginRequiredMixin, ListView):
    """User uploaded files list"""

    model = CsvFileUpload
    template_name = 'csvfileupload_list.html'
    paginate_by = 4

    def get_queryset(self):
        return CsvFileUpload.objects.filter(user=self.request.user).order_by('-upload_date')


class FilesDetailView(LoginRequiredMixin, DetailView):
    """CSV File Upload (ESO report)"""

    model = CsvFileUpload
    template_name = 'csvfileupload_detail.html'


class IndividualPricesDetailView(LoginRequiredMixin, DetailView):
    """Main ESO plan choose tables, calculations from different models,"""

    model = IndividualPrices
    template_name = 'prices.html'

    def get_object(self, queryset=None):
        csv_file_pk = self.kwargs.get('pk')
        return get_object_or_404(IndividualPrices, csv_file__pk=csv_file_pk)

    def get_context_data(self, **kwargs):
        """Update method to add calculations values to context"""


        start_time = time.time()

        context = super().get_context_data(**kwargs)
        csv_file_pk = self.kwargs.get('pk')

        # Get data from modules, convert to Pandas dataframes
        data_for_total_consumption = Calculations.objects.filter(csv_file_id=csv_file_pk).values()
        data_prices = IndividualPrices.objects.filter(csv_file_id=csv_file_pk).values()
        df_prices = pd.DataFrame(list(data_prices))
        df_totals = pd.DataFrame(list(data_for_total_consumption))

        # Total sums of consumptions
        total_p_plus = df_totals['sum_p_plus'].sum()
        total_p_minus = df_totals['sum_p_minus'].sum()
        total_pv_generated = df_totals['pv_generated'].sum()
        month_count = df_totals['sum_p_plus'].count()

        # Second table data
        total_total_consumption = int(max(0, total_pv_generated - total_p_minus) + total_p_plus)
        direct_consumption = int(max(0, total_pv_generated - total_p_minus))
        direct_consumption_percent = max(0, round((1 - total_p_minus / total_pv_generated) * 100, 2))
        avg_generation_month = int(total_pv_generated / month_count)
        avg_p_minus_month = int(total_p_minus / month_count)
        avg_p_plus_month = int(total_p_plus / month_count)
        avg_total_month = int(total_total_consumption / month_count)
        avg_direct_month = int(direct_consumption / month_count)

        # Sums for Final table (third)
        eu_kwh_plan = round(min(total_p_plus, total_p_minus) * df_prices.loc[0, 'price_kwh'], 2)
        eu_kw_plan = round(df_prices.loc[0, 'price_kw'] * df_prices.loc[0, 'plant_power'] * month_count, 2)
        missing_kwh_first = abs(min(0, total_p_minus - total_p_plus))
        missing_kwh_third = int(
            abs(min(0, total_p_minus * (100 - df_prices.loc[0, 'price_percent']) / 100 - total_p_plus)))
        eu_buy_first = abs(round(missing_kwh_first * df_prices.loc[0, 'supplier_price'], 2))
        eu_buy_third = abs(round(missing_kwh_third * df_prices.loc[0, 'supplier_price'], 2))
        unused_kwh_first = max(0, total_p_minus - total_p_plus)
        unused_kwh_third = int(max(0, total_p_minus * (100 - df_prices.loc[0, 'price_percent']) / 100 - total_p_plus))
        eu_sell_first = round(unused_kwh_first * df_prices.loc[0, 'sell_price'], 2)
        eu_sell_third = round(unused_kwh_third * df_prices.loc[0, 'sell_price'], 2)
        balance_first = round(eu_kwh_plan + eu_buy_first - eu_sell_first, 2)
        balance_second = round(eu_kw_plan + eu_buy_first - eu_sell_first, 2)
        balance_third = round(eu_buy_third - eu_sell_third, 2)

        best_plan = 0
        if balance_third < balance_first and balance_third < balance_second:
            best_plan = 3
        elif balance_second < balance_first and balance_second < balance_third:
            best_plan = 2
        elif balance_first < balance_second and balance_first < balance_third:
            best_plan = 1

        context['total_p_plus'] = total_p_plus
        context['total_p_minus'] = total_p_minus
        context['total_pv_generated'] = total_pv_generated
        context['month_count'] = month_count

        context['total_total_consumption'] = total_total_consumption
        context['direct_consumption'] = direct_consumption
        context['direct_consumption_percent'] = direct_consumption_percent
        context['avg_generation_month'] = avg_generation_month
        context['avg_p_minus_month'] = avg_p_minus_month
        context['avg_p_plus_month'] = avg_p_plus_month
        context['avg_total_month'] = avg_total_month
        context['avg_direct_month'] = avg_direct_month

        context['eu_kwh_plan'] = eu_kwh_plan
        context['eu_kw_plan'] = eu_kw_plan
        context['missing_kwh_first'] = missing_kwh_first
        context['missing_kwh_third'] = missing_kwh_third
        context['eu_buy_first'] = eu_buy_first
        context['eu_buy_third'] = eu_buy_third
        context['unused_kwh_first'] = unused_kwh_first
        context['unused_kwh_third'] = unused_kwh_third
        context['eu_sell_first'] = eu_sell_first
        context['eu_sell_third'] = eu_sell_third
        context['balance_first'] = balance_first
        context['balance_second'] = balance_second
        context['balance_third'] = balance_third
        context['best_plan'] = best_plan
        context['csv_file_pk'] = csv_file_pk

        print(f"--- {time.time() - start_time} seconds for tables values calculations---")
        return context


@login_required
def pv_values_to_model(request):
    """Function to update PV generated kWh values"""

    request_post_list = list(request.POST.items())
    request_post_list = request_post_list[1:]
    csv_file_pk = request_post_list[0][1]
    request_post_list = request_post_list[1:]
    for key, value in request_post_list:
        if value == '':
            pass
        else:
            user_value_update = Calculations.objects.get(id=key)
            user_value_update.pv_generated = value
            user_value_update.save()
    messages.success(request, "PV Generated values updated successfully!")

    html_link = reverse('pv_gen', args=[csv_file_pk])
    html_link = f'{html_link}#start'
    return redirect(html_link)


@login_required
def update_prices(request, pk):
    """Function to edit IndividualPrices model data"""

    instance = get_object_or_404(IndividualPrices, pk=pk)
    csv_file_pk = instance.csv_file.pk
    html_link = reverse('price', args=[csv_file_pk])
    html_link = f'{html_link}#start'

    if request.method == 'POST':
        form = IndividualPricesForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Data update success!")
            return redirect(html_link)
    else:
        form = IndividualPricesForm(instance=instance)
    context = {
        'form': form,
        'csv_file_pk': csv_file_pk
    }
    return render(request, 'update_prices.html', context)


@login_required
def delete_csvfile_upload(request, pk):
    """Function to delete MainPrices model object"""

    instance = get_object_or_404(CsvFileUpload, pk=pk)
    instance.delete()
    messages.success(request, f'Deleted! ')
    return redirect('list')

@staff_member_required
def upload_nord_pool_document(request):
    """Nord pool data upload to model"""

    start_time = time.time()

    if request.method == 'POST':
        form = NordPoolUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save()

            # CSV and model data to Pandas, check for existing data in model, update with only new.
            df = pd.read_csv(document.nord_pool_csv_file, sep=',')
            df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize('UTC')
            df['Date'] = df['Date'].dt.tz_convert('Europe/Vilnius')
            dates_in_db = NordPoolData.objects.all().values()
            if dates_in_db:
                df_from_db = pd.DataFrame(list(dates_in_db))
                df_from_db['date'] = df_from_db['date'].dt.tz_convert('Europe/Vilnius')
                df = pd.merge(df, df_from_db, left_on='Date', right_on='date', how='left')
                df = df[df['date'].isnull()]

            df_to_storage = []
            if df.empty:
                messages.error(request, f"There no newer data in uploaded file")
                pass
            else:
                for _, row in df.iterrows():
                    df_to_storage.append(NordPoolData(
                        date=row['Date'],
                        price=row['Nord Pool Price']
                    ))
                NordPoolData.objects.bulk_create(df_to_storage)
                count = len(df_to_storage)
                messages.success(request, f"Nord Pool data uploaded, {count} new values in database")
                print(f"--- {time.time() - start_time} seconds for Nord Poll data update---")

            return redirect('nord_pool')
    else:
        form = NordPoolUploadForm()

    context = {
        'form': form,
    }
    return render(request, 'upload_nord_pool.html', context)


@login_required
def netbilling_simulation(request, pk):
    """Function calculate netbilling simuliation"""

    start_time = time.time()
    user_end_date = PandasStorage.objects.filter(csv_file_id=pk).latest('date_time').date_time
    user_start_date = PandasStorage.objects.filter(csv_file_id=pk).earliest('date_time').date_time
    raw_data = PandasStorage.objects.filter(csv_file_id=pk).values()
    df_raw_data = pd.DataFrame(list(raw_data))

    try:
        end_date = NordPoolData.objects.latest('date').date
        start_date = NordPoolData.objects.earliest('date').date
        nord_pool = NordPoolData.objects.all().values()
        df_nord_pool = pd.DataFrame(list(nord_pool))

        df = pd.merge(df_raw_data, df_nord_pool, left_on='date_time', right_on='date', how='left')
        df = df[df['energy_type'].isin(['P+', 'P-'])]
        df['multiply'] = df['consumption_kwh'] * df['price'] / 1000

        # Calculations by months and energy type and total
        monthly_group = df.groupby([df['date_time'].dt.year,
                                    df['date_time'].dt.month,
                                    df['energy_type']])

        monthly_sum = monthly_group['multiply'].sum().unstack()

        total_sum_p_plus = round(monthly_sum['P+'].sum(), 2)
        total_sum_p_minus = round(monthly_sum['P-'].sum() * -1, 2)
        total_balance = round(total_sum_p_plus + total_sum_p_minus, 2)

        monthly_data = []
        for date_index, row in monthly_sum.iterrows():
            year = date_index[0]
            month = date_index[1]
            date = datetime.date(year, month, 1)
            monthly_data.append({
                'date': date,
                'p_plus': round(row['P+'], 2),
                'p_minus': round(row['P-'] * -1, 2),
            })

        spend_time = time.time() - start_time
        print(f"--- {spend_time} seconds for netbilling simulation---")

        context = {
            'monthly_data': monthly_data,
            'total_sum_p_plus': total_sum_p_plus,
            'total_sum_p_minus': total_sum_p_minus,
            'total_balance': total_balance,
            'spend_time': spend_time,
            'end_date': end_date,
            'start_date': start_date,
            'user_end_date': user_end_date,
            'user_start_date': user_start_date,
        }
    except ObjectDoesNotExist:
        messages.error(request, f'Ask ADMIN to upload "Nord Pool" prices! ')

        return redirect('list')

    return render(request, 'netbilling.html', context)

@staff_member_required
def enter_main_prices(request):
    """Function to enter MainPrices model data"""

    if request.method == 'POST':
        form = MainPricesForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = MainPricesForm()
    context = {
        'form': form,
    }
    return render(request, 'main_prices.html', context)


@staff_member_required
def update_main_prices(request, pk):
    """Function to edit MainPrices model data"""

    instance = get_object_or_404(MainPrices, pk=pk)
    if request.method == 'POST':
        form = MainPricesForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Data update success!")
            return redirect('main_prices_list')
    else:
        form = MainPricesForm(instance=instance)
    context = {
        'form': form,
    }
    return render(request, 'update_main_prices.html', context)

@staff_member_required
def delete_main_price(request, pk):
    """Function to delete MainPrices model object"""

    instance = get_object_or_404(MainPrices, pk=pk)
    instance.delete()
    messages.success(request, f'Deleted! ')
    return redirect('main_prices_list')


class MainPricesListView(UserPassesTestMixin, ListView):

    model = MainPrices
    template_name = 'main_prices_list.html'

    def test_func(self):
        return self.request.user.is_staff


