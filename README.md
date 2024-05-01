# ESO_analyzer 

**This is an ESO report analyzer to choose the best plan for PV plant users**

Just generate an hourly or 15-minutes report on ESO at https://mano.eso.lt/ and upload it to the site

**Instaliation**

Ensure you have Python installed
Project was created with Python 3.12

*Example for windows terminal:*

- Clone a repository to your directory with:  
git clone https://github.com/tvogulis/Analyzer_ESO

- Enter directory:  
  cd Analyzer_ESO

- Create a virtual environment:  
  python -m venv venv

- Activate the virtual environment:  
  venv\Scripts\activate.bat

- Install the Python packages listed in `requirements.txt:  
  pip install -r requirements.txt

- Prepare new database migrations and migrate:  
  python manage.py makemigrations
  python manage.py migrate

- Create superuser i.e. 'admin':  
  python manage.py createsuperuser

**Instaliation finished, now run Django development server**  
python manage.py runserver

*************
**admin** post-installation steps required
*************
- **First**    
Login and upload Nord Pool prices CSV file "Nord_Pool 2022-01-01_2024-05-01.csv".  
Afer some time you probably will need update, use python script "nord_pool_data.py", just run it and enter start/end dates it will generate new CSV file.   
- **Second**   
Enter new default values for users. Example:    
<https://github.com/tvogulis/Analyzer_ESO/blob/main/default_values_for_users.png>

*************
Short instruction for users
*************

- Register
- Login
- Generate ESO report at <https://mano.eso.lt/> for the period you want calculations for. Like example for a 12-month period. It could be hourly or 15-minutes report.
- Upload ESO generated report, use UPLOAD NEW CSV, write description
- Enter to LIST UPLOADED DOCUMENTS
- ENTER PV GENERATED KWH month by month, this will help more accurate calculate data 
- Enter CALCULATIONS, here you need EDIT YOUR DATA. **MUST ENTER YOUR PV power kW ar ESO** all other data just for more detail results.
- Enjoy many numbers :)

- Additional function is NET BILLING SIMULATION it will show you how your balance would look with selling and buying electricity in Nord Pool market.
  
