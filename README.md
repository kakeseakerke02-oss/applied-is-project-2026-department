# Кафедраның бағалау құралдары қоры

**Пән:** Ақпараттық жүйелердің қолданбалы бағдарламалық қамтылымы.
**Кезең:** 1 және 2-зертханалық жұмыстар — жобалау, жоба құрылымы және ORM деректер базасы.

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
    models.py                   6 SQLModel класы, кілттер және байланыстар
    db.py                       SQLite engine, init_db және get_session
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
seed.py                         Базаны құру және тестілік деректер енгізу
verify.py                       Бөлек уақытша базада тексеру
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
Интерфейс: http://localhost:8501 . Толық CRUD кейінгі жұмыстарда жасалады.
Базаны құру мен толтыру үшін төмендегі 2-зертхана командаларын орындаңыз.
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

## 2 зертханалық жұмыс

SQLModel арқылы реляциялық база жасалды. Кодтағы ағылшынша идентификаторлар
диаграммадағы қазақша нысандарға сәйкес келеді:

| Python класы | SQL кестесі | Міндеті | Демо жазба саны |
| --- | --- | --- | --- |
| Department | department | Кафедра | 3 |
| Teacher | teacher | Оқытушы | 3 |
| Discipline | discipline | Пән | 3 |
| AssessmentTool | assessmenttool | Бағалау құралы | 5 |
| Criterion | criterion | Бағалау критерийі | 5 |
| TeacherDisciplineLink | teacherdisciplinelink | Оқытушы мен пәннің N:M байланысы | 5 |

### Екінші жұмыстың ER схемасы
![ЛР2 алты кестеден тұратын схема](docs/er_diagram_lab2.png)

Өңделетін файл: [ER схемасы](docs/er_diagram_lab2.drawio).
Бірінші жұмыстың схемасы жоғарыда сақталды. Екінші жұмыста N:M байланысын
көрсету үшін TeacherDisciplineLink аралық кестесі қосылды. Құрал авторы
Teacher.authored_tools арқылы, ал пән жүргізетін оқытушылар
Teacher.disciplines ↔ Discipline.teachers арқылы байланысады. Бұл — екі
бөлек ұғым: авторлық және пәнді оқыту.

### Орындау командалары
Жоба папкасындағы PowerShell ішінде:
```powershell
.\venv\Scripts\python.exe seed.py
.\venv\Scripts\python.exe verify.py
```
Бірінші команда жоба түбірінде database.db жасап, барлық кестеге бастапқы
деректер енгізеді. echo=True болғандықтан CREATE TABLE, INSERT және басқа
SQL командалары консольде көрінеді. Қайта орындағанда бұрынғы демо жазбалар
қайталанбайды. Ойдан алынған оқытушылар үшін example.com мекенжайлары қолданылды.
verify.py бөлек уақытша база жасайды, қолданыстағы database.db файлын өзгертпейді.
Соңында PASS шығады. Шектеулерді тексергенде күтілетін қате енгізулер кері
қайтарылады; бұл тексерудің қалыпты бөлігі.

### Модельдерді түсіндіру
- table=True Python класын SQL кестесімен байланыстырады; объект бір жазбаға сәйкес келеді.
- id — алғашқы кілт; department_id және басқа FK өрістері нақты SQL бағандары.
- department, teachers, criteria сияқты Relationship атрибуттары — Python объектілерімен жұмыс істеу жолы; қосымша SQL бағандары емес.
- back_populates қарсы модельдегі байланыс атрибутын атайды.
- TeacherDisciplineLink екі FK өрісінен тұрады. Екеуі бірге алғашқы кілт,
  сондықтан бір оқытушы–пән жұбы екі рет сақталмайды.
- SQL кестесіндегі UNIQUE, FOREIGN KEY және CHECK шектеулері дерек бүтіндігін сақтайды.
- Criterion.max_score — Decimal; базада нөлден үлкен болуын CHECK тексереді.
- AssessmentTool.total_score() критерийлердің максималды балдарын қосады.
  Бұл әдісті сессия ашық кезде, criteria байланысы қолжетімді болғанда шақырыңыз.
- Құрал ORM арқылы өшірілсе, критерийлері бірге өшіріледі. Пән мен авторға
  сілтемелер FK арқылы қорғалған; еркін каскадты өшіру қолданылмайды.
- created_at Python жағында UTC арқылы жасалады; SQLite уақыт белдеуін бөлек сақтамайды.
- create_all кестелерді жасайды, бірақ бар кестелердің бағандарын өзгертпейді.
  Схема өзгерсе, нақты жобада миграциялар қолданылады.

### Git арқылы сақтау
```powershell
git add app/database/ seed.py verify.py docs/ README.md
git commit -m "feat: add SQLModel ORM models and database seed script"
git push origin main
```
seed.py түбірде орналасқандықтан, тек git add app/ командасы жеткіліксіз.
database.db және venv .gitignore ішінде: олар репозиторийге жіберілмейді.
Басқа компьютерде орта requirements.txt арқылы, база seed.py арқылы қайта құрылады.

### Бақылау сұрақтарына қысқа жауаптар
1. ORM Python объектілері мен SQL кестелерін сәйкестендіріп, қайталанатын
   SQL кодын азайтады. Python класы — деректер сипаттамасы, SQL кестесі —
   деректер базасындағы нақты жолдар, бағандар және шектеулер.
2. department_id SQL ішінде сақталатын FK; department байланысты объектіні
   Python жағында алуға арналған Relationship.
3. Seeding тест пен көрсетілімге арналған бастапқы деректерді енгізеді.
   Бос базада байланыстарды және есептеулерді тексеру қиын.
4. echo=True орындалған SQL командалары мен параметрлерін консольге шығарады.
5. database.db өзгермелі жергілікті деректерді сақтайды, ал models.py —
   қайта жасалатын схеманың бастапқы коды. Код Git ішінде сақталады, база файлы жіберілмейді.

ИИ сұраныстары: [lab2_ai_prompts.txt](docs/lab2_ai_prompts.txt).
Ресми анықтамалар:
[SQLModel екі жақты байланыстары](https://sqlmodel.tiangolo.com/tutorial/relationship-attributes/back-populates/),
[SQLModel N:M байланысы](https://sqlmodel.tiangolo.com/tutorial/many-to-many/create-models-with-link/).
