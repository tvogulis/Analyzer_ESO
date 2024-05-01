from django import forms

from .models import CsvFileUpload, IndividualPrices, NordPool, MainPrices


class CsvFileUploadForm(forms.ModelForm):
    class Meta:
        model = CsvFileUpload
        fields = ['csv_file', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['csv_file'].widget.attrs.update({'accept': '.csv'})

class IndividualPricesForm(forms.ModelForm):
    class Meta:
        model = IndividualPrices
        fields = ['price_kwh', 'price_kw', 'price_percent', 'supplier_price', 'sell_price', 'plant_power']


class NordPoolUploadForm(forms.ModelForm):
    class Meta:
        model = NordPool
        fields = ['nord_pool_csv_file',]


class MainPricesForm(forms.ModelForm):
    class Meta:
        model = MainPrices
        fields = '__all__'

