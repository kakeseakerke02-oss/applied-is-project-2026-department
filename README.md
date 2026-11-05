# Кафедраның бағалау құралдары қоры

**Пән:** Ақпараттық жүйелердің қолданбалы бағдарламалық қамтылымы.
**Кезең:** 1-зертханалық жұмыс — жобалау және жобаның бастапқы құрылымы.

## Пәндік облыс
Жүйе кафедраның пәндер бойынша бағалау материалдарын бір жерге жинауға арналған.
Негізгі пайдаланушысы — оқытушы. Бағалау құралдарына тест, емтихан сұрақтары,
практикалық тапсырма және зертханалық жұмыс жатады. Әр құралдың пәні, авторы,
мазмұны және бағалау критерийлері болады. Осы кезеңде деректер құрылымы
жобаланып, қолданбаның бастапқы файлдары дайындалды.

## ER диаграммасы
![Кафедра қорының ER диаграммасы](docs/er_diagram.png)

- Кафедра → Оқытушы: 1:N.
- Кафедра → Пән: 1:N.
- Пән → Бағалау құралы: 1:N.
- Оқытушы → Бағалау құралы: 1:N, оқытушы — автор.
- Бағалау құралы → Бағалау критерийі: 1:N.

Әр бағынышты жазба бір ата-аналық жазбаға тиесілі; ата-ананың 0 немесе одан
көп бағынышты жазбасы болуы мүмкін. Құралдың максималды балы оның
критерийлерінің максималды балдарының қосындысымен анықталады.
Өңделетін нұсқа — docs/diagrams.drawio. Оны diagrams.net сайтында ашыңыз.
Қосымша кластар мен тізбектік диаграммалар жобаланатын әрекеттерді көрсетеді.

## Жоба құрылымы
```text
app/
  main.py                       FastAPI кіріс нүктесі
  database/
    models.py                   ORM модельдеріне арналған файл
    db.py                       База қосылымына арналған файл
  routers/
    assessment_tools.py         API маршруттарына арналған файл
  frontend/
    ui.py                       Streamlit интерфейсінің қаңқасы
docs/
  er_diagram.png                ER диаграммасы
  class_diagram.png             Кластар диаграммасы
  sequence_diagram.png          Тізбектік диаграмма
  diagrams.drawio               Үш диаграмманың өңделетін нұсқасы
  ai_prompt.txt                 Жобаны жасауға арналған ИИ сұранысы
requirements.txt                Python тәуелділіктері
.gitignore                      Git-ке қосылмайтын файлдар
README.md                       Жобаның сипаттамасы
```

## Құралдар және IDE
Python 3.11+, FastAPI, Uvicorn, SQLModel, Streamlit, Git.
ИИ көмегімен жоба құрылымы мен диаграммалар дайындалды. Cursor немесе
VS Code пен ИИ кеңейтімінде осы папканы ашыңыз. Python кеңейтімінің
«Python: Select Interpreter» командасынан venv ішіндегі Python-ды таңдаңыз.

## Windows PowerShell ішінде іске қосу
Командаларды жоба папкасының түбірінен орындаңыз:
```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```
Сервер: http://127.0.0.1:8000/ . Құжаттама: http://127.0.0.1:8000/docs .
Тоқтату: Ctrl+C. Streamlit қаңқасы бөлек терминалда іске қосылады:
```powershell
.\venv\Scripts\python.exe -m streamlit run app/frontend/ui.py
```
Интерфейс: http://localhost:8501 . Толық CRUD пен база келесі жұмыстарда жасалады.
Ортаны белсендіру командасы: `.\venv\Scripts\Activate.ps1`.
Белсендіру орындалмаса, жоғарыдағыдай venv Python-ын тікелей шақырыңыз.

## Git
Репозиторийді клондау:
```powershell
git clone https://github.com/kakeseakerke02-oss/applied-is-project-2026-department.git
cd applied-is-project-2026-department
```
Өзгерістерді сақтау:
```powershell
git add .
git commit -m "feat: initial project structure with AI assist"
git push origin main
```
venv/, database.db, .env және Python кэші Git-ке қосылмайды.

## Қорғауға дайындық
venv кітапханаларды бөледі. requirements.txt ортаны қайта орнатуға мүмкіндік
береді. git commit жергілікті нұсқаны сақтайды, git push оны қашықтағы
репозиторийге жібереді. main.py серверді ашады, database — деректер қабаты,
routers — API, frontend — пайдаланушы интерфейсі.
