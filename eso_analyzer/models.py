from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class CsvFileUpload(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    csv_file = models.FileField(upload_to='uploads/%Y/%m/')
    description = models.CharField('Description', max_length=255, null=True)

    def __str__(self):
        return f"Document {self.csv_file.name}"

class PandasStorage(models.Model):
    csv_file = models.ForeignKey('CsvFileUpload', on_delete=models.CASCADE)
    power_kw = models.IntegerField('Power', null=True)
    date_time = models.DateTimeField('DateTime', null=True)
    energy_type = models.CharField('Type', max_length=2, null=True)
    consumption_kwh = models.FloatField('Consumption', null=True)

class Calculations(models.Model):
    csv_file = models.ForeignKey('CsvFileUpload', on_delete=models.CASCADE)
    date = models.DateField('DateTime', null=True)
    sum_p_plus = models.IntegerField('P+', null=True)
    sum_p_minus = models.IntegerField('P-', null=True)
    sum_q_plus = models.IntegerField('Q+', null=True)
    sum_q_minus = models.IntegerField('Q-', null=True)
    pv_generated = models.IntegerField('PV', default=0)

    def __str__(self):
        return f'{self.date} ({self.sum_p_plus})'

class MainPrices(models.Model):
    date = models.DateField('DateTime', null=True)
    price_kwh = models.FloatField('Price kWh', null=True, help_text='Price for recovered kWh')
    price_kw = models.FloatField('Price kW', null=True, help_text='Price for power rate per kW')
    price_percent = models.IntegerField('Percent of kWh', null=True, help_text='Percent of kWh')
    supplier_price = models.FloatField('Price kWh buy', null=True, help_text='Price kWh if need to buy from supplier')
    supplier_price_day = models.FloatField('Price kWh buy day', null=True, help_text='Price kWh if need to buy from supplier day tariff')
    supplier_price_night = models.FloatField('Price kWh buy night', null=True, help_text='Price kWh if need to buy from supplier night tariff')
    sell_price = models.FloatField('Price kWh sell', null=True, help_text='Price kWh if need to sell to supplier')
    plant_power = models.FloatField('Plant power kW', null=True, default=0, help_text='PV plant power kW at ESO')

    def __str__(self):
        return f'{self.date} {self.price_kwh} {self.price_kw} {self.price_percent}'

class IndividualPrices(models.Model):
    csv_file = models.ForeignKey('CsvFileUpload', on_delete=models.CASCADE)
    date = models.DateField('DateTime', null=True)
    update_date = models.DateTimeField(auto_now=True)
    price_kwh = models.FloatField('Price kWh', null=True, help_text='Price for recovered kWh')
    price_kw = models.FloatField('Price kW', null=True, help_text='Price for power rate per kW')
    price_percent = models.IntegerField('Percent of kWh', null=True, help_text='Percent of kWh')
    supplier_price = models.FloatField('Price kWh buy', null=True, help_text='Price kWh if need to buy from supplier')
    supplier_price_day = models.FloatField('Price kWh buy day', null=True, help_text='Price kWh if need to buy from supplier day tariff')
    supplier_price_night = models.FloatField('Price kWh buy night', null=True, help_text='Price kWh if need to buy from supplier night tariff')
    sell_price = models.FloatField('Price kWh sell', null=True, help_text='Price kWh if need to sell to supplier')
    plant_power = models.FloatField('Plant power kW', null=True, default=0, validators=[MinValueValidator(0, 'PV power can not be negative')], help_text='PV plant power kW at ESO')


    def __str__(self):
        return f'{self.date} {self.update_date} {self.price_kwh} {self.price_kw} {self.price_percent}'


class NordPool(models.Model):
    nord_pool_csv_file = models.FileField(upload_to='nord_pool/%Y/%m/')

class NordPoolData(models.Model):
    date = models.DateTimeField('DateTime', null=True)
    price = models.FloatField('Price', null=True, help_text='Nord Pool price of MWh')


