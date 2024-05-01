from django.urls import path

from .views import (
    index, register, upload_csv_document, pv_values_to_model, FilesListView, FilesDetailView,
    IndividualPricesDetailView, update_prices, upload_nord_pool_document, netbilling_simulation, enter_main_prices,
    MainPricesListView, update_main_prices, delete_main_price, delete_csvfile_upload
)

urlpatterns = [
    path('', index, name='index'),
    path('register/', register, name='register'),
    path('upload/', upload_csv_document, name='upload'),
    path('upload_nord_pool/', upload_nord_pool_document, name='nord_pool'),
    path('pv_values_to_model/', pv_values_to_model, name='pv_values_to_model'),
    path('list/', FilesListView.as_view(), name='list'),
    path('list/<int:pk>/pv_gen/', FilesDetailView.as_view(), name='pv_gen'),
    path('list/<int:pk>/price/', IndividualPricesDetailView.as_view(), name='price'),
    path('list/<int:pk>/price_update/', update_prices, name='update_price'),
    path('list/<int:pk>/netbilling/', netbilling_simulation, name='netbilling'),
    path('main_prices/', enter_main_prices, name='main_prices'),
    path('main_prices_list/', MainPricesListView.as_view(), name='main_prices_list'),
    path('main_prices_list/<int:pk>', update_main_prices, name='update_main_prices'),
    path('main_prices_delete/<int:pk>/', delete_main_price, name='delete_main_price'),
    path('delete_csvfile_upload/<int:pk>/', delete_csvfile_upload, name='delete_csvfile_upload'),
]
