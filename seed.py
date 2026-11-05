"""Жоба түбірінен іске қосу: python seed.py. Қайта орындау қауіпсіз."""

from decimal import Decimal

from sqlmodel import Session, select

from app.database.db import DB_PATH, engine, init_db
from app.database.models import Department, Teacher, Discipline, AssessmentTool, Criterion


def seed(db_engine=None):
    target = engine if db_engine is None else db_engine
    init_db(target)
    with Session(target) as session:
        # Қате болса, бүкіл бастапқы толтыру кері қайтарылады.
        with session.begin():
            departments = {}
            for code, name in [
                ("IS", "Ақпараттық жүйелер кафедрасы"),
                ("SE", "Бағдарламалық инженерия кафедрасы"),
                ("MATH", "Математика кафедрасы"),
            ]:
                obj = session.exec(select(Department).where(Department.code == code)).first()
                if obj is None:
                    obj = Department(code=code, name=name)
                    session.add(obj)
                    session.flush()
                departments[code] = obj

            teachers = {}
            for email, name, dept in [
                ("a.serik@example.com", "Айдана Серікқызы", "IS"),
                ("b.nurlan@example.com", "Бекзат Нұрланұлы", "SE"),
                ("d.aman@example.com", "Дана Аманқызы", "MATH"),
            ]:
                obj = session.exec(select(Teacher).where(Teacher.email == email)).first()
                if obj is None:
                    obj = Teacher(email=email, full_name=name, department=departments[dept])
                    session.add(obj)
                    session.flush()
                teachers[email] = obj

            disciplines = {}
            for code, name, dept in [
                ("DB101", "Деректер базасы", "IS"),
                ("PY101", "Python бағдарламалау", "SE"),
                ("DM101", "Дискретті математика", "MATH"),
            ]:
                obj = session.exec(select(Discipline).where(Discipline.code == code)).first()
                if obj is None:
                    obj = Discipline(code=code, name=name, department=departments[dept])
                    session.add(obj)
                    session.flush()
                disciplines[code] = obj

            # 5 байланыс: бір оқытушыда бірнеше пән және бір пәнде бірнеше оқытушы.
            for email, code in [
                ("a.serik@example.com", "DB101"),
                ("a.serik@example.com", "PY101"),
                ("b.nurlan@example.com", "PY101"),
                ("d.aman@example.com", "DM101"),
                ("d.aman@example.com", "DB101"),
            ]:
                teacher, discipline = teachers[email], disciplines[code]
                if discipline not in teacher.disciplines:
                    teacher.disciplines.append(discipline)

            rows = [
                ("DB101", "a.serik@example.com", "SQL негіздері тесті", "Тест",
                 "SELECT, WHERE және JOIN тақырыптары бойынша 20 сұрақ.",
                 "20 сұрақтың әр дұрыс жауабына 1 балл", "20.00"),
                ("DB101", "a.serik@example.com", "ER модель құру", "Зертханалық жұмыс",
                 "Бес нысаннан тұратын база схемасын және байланыстарын жобалау.",
                 "Нысандар, кілттер және байланыстардың дұрыстығы", "30.00"),
                ("PY101", "b.nurlan@example.com", "Python функциялары", "Практикалық тапсырма",
                 "Параметрлері және қайтарылатын мәні бар 5 функция жазу.",
                 "Функциялардың талапқа сай орындалуы", "25.00"),
                ("PY101", "a.serik@example.com", "ORM модельдері", "Зертханалық жұмыс",
                 "SQLModel арқылы алғашқы және сыртқы кілттері бар модельдер жасау.",
                 "Модельдер мен екі жақты байланыстардың дұрыстығы", "40.00"),
                ("DM101", "d.aman@example.com", "Графтар теориясы", "Емтихан",
                 "Графтың төбелері, қырлары және жолдары бойынша 5 есеп шығару.",
                 "Есептердің шешімі мен негіздемесінің дұрыстығы", "50.00"),
            ]
            for code, email, title, kind, content, description, score in rows:
                discipline, author = disciplines[code], teachers[email]
                obj = session.exec(select(AssessmentTool).where(
                    AssessmentTool.discipline_id == discipline.id,
                    AssessmentTool.author_id == author.id,
                    AssessmentTool.title == title,
                )).first()
                if obj is None:
                    obj = AssessmentTool(discipline=discipline, author=author,
                                         title=title, tool_type=kind, content=content)
                    session.add(obj)
                    session.flush()
                criterion = session.exec(select(Criterion).where(
                    Criterion.assessment_tool_id == obj.id,
                    Criterion.description == description,
                )).first()
                if criterion is None:
                    session.add(Criterion(assessment_tool=obj, description=description,
                                          max_score=Decimal(score)))
    print("SEED OK: demo records saved; existing records preserved.")


if __name__ == "__main__":
    seed()
    print(f"Database: {DB_PATH}")
