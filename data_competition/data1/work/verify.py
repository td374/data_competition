import sys
sys.stdout.reconfigure(encoding='utf-8')
packages = ['akshare','pdfplumber','docx','sklearn','xgboost','lightgbm','shap','seaborn','yaml','streamlit','statsmodels','pandas','numpy','matplotlib','openpyxl','PyPDF2','tqdm','requests','bs4','xlrd','PIL','scipy','numba']
for p in packages:
    try:
        __import__(p)
        print(f'  OK  {p}')
    except Exception as e:
        print(f'FAIL {p}: {e}')
