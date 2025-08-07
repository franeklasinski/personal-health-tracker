from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
import os
from werkzeug.utils import secure_filename
import plotly.graph_objs as go
import plotly.utils
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'twoj-secret-key-tutaj'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dziennik.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('instance', exist_ok=True)

db = SQLAlchemy(app)

# Modele bazy danych
class SportEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    activity = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer)  # w minutach
    notes = db.Column(db.Text)
    photo_filename = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NutritionEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    meal_type = db.Column(db.String(50), nullable=False)  # śniadanie, obiad, kolacja, przekąska
    food_item = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.String(100))
    calories = db.Column(db.Integer)
    water_ml = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PersonalData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    weight = db.Column(db.Float)
    height = db.Column(db.Float)  # w cm
    body_fat = db.Column(db.Float)  # procent
    muscle_mass = db.Column(db.Float)  # kg
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def bmi(self):
        if self.weight and self.height:
            height_m = self.height / 100
            return round(self.weight / (height_m * height_m), 1)
        return None

# Funkcje pomocnicze
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_weight_chart():
    data = PersonalData.query.order_by(PersonalData.date).all()
    if not data:
        return None
    
    dates = [entry.date for entry in data if entry.weight]
    weights = [entry.weight for entry in data if entry.weight]
    
    if not dates:
        return None
    
    fig = go.Figure(data=go.Scatter(x=dates, y=weights, mode='lines+markers'))
    fig.update_layout(
        title='Wykres Wagi',
        xaxis_title='Data',
        yaxis_title='Waga (kg)',
        height=400
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def create_bmi_chart():
    data = PersonalData.query.order_by(PersonalData.date).all()
    if not data:
        return None
    
    dates = []
    bmis = []
    
    for entry in data:
        if entry.bmi:
            dates.append(entry.date)
            bmis.append(entry.bmi)
    
    if not dates:
        return None
    
    fig = go.Figure(data=go.Scatter(x=dates, y=bmis, mode='lines+markers'))
    fig.update_layout(
        title='Wykres BMI',
        xaxis_title='Data',
        yaxis_title='BMI',
        height=400
    )
    
    # Dodaj linie referencyjne BMI
    fig.add_hline(y=18.5, line_dash="dash", line_color="blue", annotation_text="Niedowaga")
    fig.add_hline(y=25, line_dash="dash", line_color="green", annotation_text="Norma")
    fig.add_hline(y=30, line_dash="dash", line_color="orange", annotation_text="Nadwaga")
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def create_body_composition_chart():
    """Wykres składu ciała (tkanka tłuszczowa + masa mięśniowa)"""
    data = PersonalData.query.order_by(PersonalData.date).all()
    if not data:
        return None
    
    dates = []
    body_fat = []
    muscle_mass = []
    
    for entry in data:
        if entry.body_fat or entry.muscle_mass:
            dates.append(entry.date)
            body_fat.append(entry.body_fat if entry.body_fat else None)
            muscle_mass.append(entry.muscle_mass if entry.muscle_mass else None)
    
    if not dates:
        return None
    
    fig = go.Figure()
    
    if any(bf for bf in body_fat if bf is not None):
        fig.add_trace(go.Scatter(x=dates, y=body_fat, mode='lines+markers', 
                                name='Tkanka tłuszczowa (%)', line=dict(color='red')))
    
    if any(mm for mm in muscle_mass if mm is not None):
        fig.add_trace(go.Scatter(x=dates, y=muscle_mass, mode='lines+markers', 
                                name='Masa mięśniowa (kg)', line=dict(color='green'), yaxis='y2'))
    
    fig.update_layout(
        title='Skład Ciała',
        xaxis_title='Data',
        yaxis=dict(title='Tkanka tłuszczowa (%)', side='left'),
        yaxis2=dict(title='Masa mięśniowa (kg)', side='right', overlaying='y'),
        height=400,
        legend=dict(x=0, y=1)
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def create_calories_chart():
    """Wykres dziennego spożycia kalorii"""
    from sqlalchemy import func
    
    # Grupowanie kalorii po dniach
    calories_by_day = db.session.query(
        NutritionEntry.date,
        func.sum(NutritionEntry.calories).label('total_calories')
    ).filter(NutritionEntry.calories.isnot(None))\
     .group_by(NutritionEntry.date)\
     .order_by(NutritionEntry.date)\
     .all()
    
    if not calories_by_day:
        return None
    
    dates = [entry.date for entry in calories_by_day]
    calories = [entry.total_calories for entry in calories_by_day]
    
    fig = go.Figure(data=go.Bar(x=dates, y=calories, marker_color='orange'))
    fig.update_layout(
        title='Dzienne Spożycie Kalorii',
        xaxis_title='Data',
        yaxis_title='Kalorie (kcal)',
        height=400
    )
    
    avg_calories = sum(calories) / len(calories) if calories else 0
    fig.add_hline(y=avg_calories, line_dash="dash", line_color="red", 
                  annotation_text=f"Średnia: {avg_calories:.0f} kcal")
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def create_water_chart():
    """Wykres dziennego spożycia wody"""
    from sqlalchemy import func
    
    # Grupowanie wody po dniach
    water_by_day = db.session.query(
        NutritionEntry.date,
        func.sum(NutritionEntry.water_ml).label('total_water')
    ).filter(NutritionEntry.water_ml > 0)\
     .group_by(NutritionEntry.date)\
     .order_by(NutritionEntry.date)\
     .all()
    
    if not water_by_day:
        return None
    
    dates = [entry.date for entry in water_by_day]
    water = [entry.total_water for entry in water_by_day]
    
    fig = go.Figure(data=go.Bar(x=dates, y=water, marker_color='lightblue'))
    fig.update_layout(
        title='Dzienne Spożycie Wody',
        xaxis_title='Data',
        yaxis_title='Woda (ml)',
        height=400
    )
    
    fig.add_hline(y=2000, line_dash="dash", line_color="blue", 
                  annotation_text="Zalecane: 2000ml")
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def create_activity_chart():
    """Wykres aktywności sportowej (czas treningu)"""
    from sqlalchemy import func
    
    # Grupowanie aktywności po dniach
    activity_by_day = db.session.query(
        SportEntry.date,
        func.sum(SportEntry.duration).label('total_duration'),
        func.count(SportEntry.id).label('workout_count')
    ).filter(SportEntry.duration.isnot(None))\
     .group_by(SportEntry.date)\
     .order_by(SportEntry.date)\
     .all()
    
    if not activity_by_day:
        return None
    
    dates = [entry.date for entry in activity_by_day]
    durations = [entry.total_duration for entry in activity_by_day]
    counts = [entry.workout_count for entry in activity_by_day]
    
    fig = go.Figure()
    
    # Czas treningu (słupki)
    fig.add_trace(go.Bar(x=dates, y=durations, name='Czas treningu (min)', 
                        marker_color='green', yaxis='y'))
    
    # Liczba treningów (linia)
    fig.add_trace(go.Scatter(x=dates, y=counts, mode='lines+markers', 
                            name='Liczba treningów', line=dict(color='red'), yaxis='y2'))
    
    fig.update_layout(
        title='Aktywność Sportowa',
        xaxis_title='Data',
        yaxis=dict(title='Czas (minuty)', side='left'),
        yaxis2=dict(title='Liczba treningów', side='right', overlaying='y'),
        height=400,
        legend=dict(x=0, y=1)
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def create_meal_distribution_chart():
    """Wykres rozkładu posiłków"""
    from sqlalchemy import func
    
    # Zliczanie posiłków według typu
    meal_counts = db.session.query(
        NutritionEntry.meal_type,
        func.count(NutritionEntry.id).label('count')
    ).group_by(NutritionEntry.meal_type).all()
    
    if not meal_counts:
        return None
    
    meal_types = [entry.meal_type.title() for entry in meal_counts]
    counts = [entry.count for entry in meal_counts]
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    
    fig = go.Figure(data=go.Pie(labels=meal_types, values=counts, 
                               marker=dict(colors=colors)))
    fig.update_layout(
        title='Rozkład Rodzajów Posiłków',
        height=400
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

# Trasy
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sport')
def sport():
    entries = SportEntry.query.order_by(SportEntry.date.desc()).limit(10).all()
    return render_template('sport.html', entries=entries)

@app.route('/sport/add', methods=['GET', 'POST'])
def add_sport():
    if request.method == 'POST':
        try:
            # Walidacja danych
            if not request.form.get('date'):
                flash('Data jest wymagana!', 'error')
                return render_template('add_sport.html')
            
            if not request.form.get('activity'):
                flash('Rodzaj aktywności jest wymagany!', 'error')
                return render_template('add_sport.html')
            
            entry = SportEntry(
                date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
                activity=request.form['activity'],
                duration=int(request.form['duration']) if request.form.get('duration') else None,
                notes=request.form.get('notes', '')
            )
            
            # Obsługa zdjęcia
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    name, ext = os.path.splitext(filename)
                    filename = f"{timestamp}_{name}{ext}"
                    
                    upload_path = os.path.join(app.config['UPLOAD_FOLDER'])
                    os.makedirs(upload_path, exist_ok=True)
                    
                    file_path = os.path.join(upload_path, filename)
                    file.save(file_path)
                    entry.photo_filename = filename
                elif file and file.filename and not allowed_file(file.filename):
                    flash('Nieprawidłowy format pliku! Dozwolone: PNG, JPG, JPEG, GIF', 'error')
                    return render_template('add_sport.html')
            
            db.session.add(entry)
            db.session.commit()
            flash('Wpis sportowy został dodany!', 'success')
            return redirect(url_for('sport'))
            
        except ValueError as e:
            flash('Błąd w dacie lub liczbach!', 'error')
            return render_template('add_sport.html')
        except Exception as e:
            flash(f'Wystąpił błąd: {str(e)}', 'error')
            return render_template('add_sport.html')
    
    return render_template('add_sport.html')

@app.route('/sport/edit/<int:id>', methods=['GET', 'POST'])
def edit_sport(id):
    entry = SportEntry.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Walidacja danych
            if not request.form.get('date'):
                flash('Data jest wymagana!', 'error')
                return render_template('edit_sport.html', entry=entry)
            
            if not request.form.get('activity'):
                flash('Rodzaj aktywności jest wymagany!', 'error')
                return render_template('edit_sport.html', entry=entry)
            
            # Aktualizuje dane
            entry.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            entry.activity = request.form['activity']
            entry.duration = int(request.form['duration']) if request.form.get('duration') else None
            entry.notes = request.form.get('notes', '')
            
            # Obsługa nowego zdjęcia
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename and allowed_file(file.filename):
              
                    if entry.photo_filename:
                        old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], entry.photo_filename)
                        if os.path.exists(old_file_path):
                            os.remove(old_file_path)
                    
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    name, ext = os.path.splitext(filename)
                    filename = f"{timestamp}_{name}{ext}"
                    
                    upload_path = os.path.join(app.config['UPLOAD_FOLDER'])
                    os.makedirs(upload_path, exist_ok=True)
                    
                    file_path = os.path.join(upload_path, filename)
                    file.save(file_path)
                    entry.photo_filename = filename
                elif file and file.filename and not allowed_file(file.filename):
                    flash('Nieprawidłowy format pliku! Dozwolone: PNG, JPG, JPEG, GIF', 'error')
                    return render_template('edit_sport.html', entry=entry)
            
            db.session.commit()
            flash('Wpis sportowy został zaktualizowany!', 'success')
            return redirect(url_for('sport'))
            
        except ValueError as e:
            flash('Błąd w dacie lub liczbach!', 'error')
            return render_template('edit_sport.html', entry=entry)
        except Exception as e:
            flash(f'Wystąpił błąd: {str(e)}', 'error')
            return render_template('edit_sport.html', entry=entry)
    
    return render_template('edit_sport.html', entry=entry)

@app.route('/sport/delete/<int:id>', methods=['POST'])
def delete_sport(id):
    entry = SportEntry.query.get_or_404(id)
    
    try:
        if entry.photo_filename:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], entry.photo_filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        db.session.delete(entry)
        db.session.commit()
        flash('Wpis sportowy został usunięty!', 'success')
    except Exception as e:
        flash(f'Błąd podczas usuwania: {str(e)}', 'error')
    
    return redirect(url_for('sport'))

@app.route('/nutrition')
def nutrition():
    entries = NutritionEntry.query.order_by(NutritionEntry.date.desc()).limit(20).all()
    return render_template('nutrition.html', entries=entries)

@app.route('/nutrition/add', methods=['GET', 'POST'])
def add_nutrition():
    if request.method == 'POST':
        try:
            # Walidacja danych
            if not request.form.get('date'):
                flash('Data jest wymagana!', 'error')
                return render_template('add_nutrition.html')
            
            if not request.form.get('meal_type'):
                flash('Typ posiłku jest wymagany!', 'error')
                return render_template('add_nutrition.html')
                
            if not request.form.get('food_item'):
                flash('Opis posiłku jest wymagany!', 'error')
                return render_template('add_nutrition.html')
            
            entry = NutritionEntry(
                date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
                meal_type=request.form['meal_type'],
                food_item=request.form['food_item'],
                quantity=request.form.get('quantity', ''),
                calories=int(request.form['calories']) if request.form.get('calories') else None,
                water_ml=int(request.form['water_ml']) if request.form.get('water_ml') else 0,
                notes=request.form.get('notes', '')
            )
            
            db.session.add(entry)
            db.session.commit()
            flash('Wpis żywieniowy został dodany!', 'success')
            return redirect(url_for('nutrition'))
            
        except ValueError as e:
            flash('Błąd w dacie lub liczbach!', 'error')
            return render_template('add_nutrition.html')
        except Exception as e:
            flash(f'Wystąpił błąd: {str(e)}', 'error')
            return render_template('add_nutrition.html')
    
    return render_template('add_nutrition.html')

@app.route('/nutrition/edit/<int:id>', methods=['GET', 'POST'])
def edit_nutrition(id):
    entry = NutritionEntry.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Walidacja danych
            if not request.form.get('date'):
                flash('Data jest wymagana!', 'error')
                return render_template('edit_nutrition.html', entry=entry)
            
            if not request.form.get('meal_type'):
                flash('Typ posiłku jest wymagany!', 'error')
                return render_template('edit_nutrition.html', entry=entry)
                
            if not request.form.get('food_item'):
                flash('Opis posiłku jest wymagany!', 'error')
                return render_template('edit_nutrition.html', entry=entry)
            
            # Aktualizuje dane
            entry.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            entry.meal_type = request.form['meal_type']
            entry.food_item = request.form['food_item']
            entry.quantity = request.form.get('quantity', '')
            entry.calories = int(request.form['calories']) if request.form.get('calories') else None
            entry.water_ml = int(request.form['water_ml']) if request.form.get('water_ml') else 0
            entry.notes = request.form.get('notes', '')
            
            db.session.commit()
            flash('Wpis żywieniowy został zaktualizowany!', 'success')
            return redirect(url_for('nutrition'))
            
        except ValueError as e:
            flash('Błąd w dacie lub liczbach!', 'error')
            return render_template('edit_nutrition.html', entry=entry)
        except Exception as e:
            flash(f'Wystąpił błąd: {str(e)}', 'error')
            return render_template('edit_nutrition.html', entry=entry)
    
    return render_template('edit_nutrition.html', entry=entry)

@app.route('/nutrition/delete/<int:id>', methods=['POST'])
def delete_nutrition(id):
    entry = NutritionEntry.query.get_or_404(id)
    
    try:
        db.session.delete(entry)
        db.session.commit()
        flash('Wpis żywieniowy został usunięty!', 'success')
    except Exception as e:
        flash(f'Błąd podczas usuwania: {str(e)}', 'error')
    
    return redirect(url_for('nutrition'))

@app.route('/personal')
def personal():
    entries = PersonalData.query.order_by(PersonalData.date.desc()).limit(10).all()
    
    # Generowanie wszystkich wykresów
    weight_chart = create_weight_chart()
    bmi_chart = create_bmi_chart()
    body_composition_chart = create_body_composition_chart()
    calories_chart = create_calories_chart()
    water_chart = create_water_chart()
    activity_chart = create_activity_chart()
    meal_distribution_chart = create_meal_distribution_chart()
    
    return render_template('personal.html', 
                         entries=entries, 
                         weight_chart=weight_chart, 
                         bmi_chart=bmi_chart,
                         body_composition_chart=body_composition_chart,
                         calories_chart=calories_chart,
                         water_chart=water_chart,
                         activity_chart=activity_chart,
                         meal_distribution_chart=meal_distribution_chart)

@app.route('/personal/add', methods=['GET', 'POST'])
def add_personal():
    if request.method == 'POST':
        try:
            # Walidacja danych
            if not request.form.get('date'):
                flash('Data jest wymagana!', 'error')
                return render_template('add_personal.html')
            
            if not any([request.form.get('weight'), request.form.get('height'), 
                       request.form.get('body_fat'), request.form.get('muscle_mass')]):
                flash('Podaj przynajmniej jedną wartość pomiarową!', 'error')
                return render_template('add_personal.html')
            
            entry = PersonalData(
                date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
                weight=float(request.form['weight']) if request.form.get('weight') else None,
                height=float(request.form['height']) if request.form.get('height') else None,
                body_fat=float(request.form['body_fat']) if request.form.get('body_fat') else None,
                muscle_mass=float(request.form['muscle_mass']) if request.form.get('muscle_mass') else None,
                notes=request.form.get('notes', '')
            )
            
            db.session.add(entry)
            db.session.commit()
            flash('Dane osobiste zostały dodane!', 'success')
            return redirect(url_for('personal'))
            
        except ValueError as e:
            flash('Błąd w dacie lub liczbach! Sprawdź poprawność danych.', 'error')
            return render_template('add_personal.html')
        except Exception as e:
            flash(f'Wystąpił błąd: {str(e)}', 'error')
            return render_template('add_personal.html')
    
    return render_template('add_personal.html')

@app.route('/calendar')
def calendar():
    today = date.today()
    sport_entries = SportEntry.query.filter(
        SportEntry.date >= date(today.year, today.month, 1)
    ).all()
    
    nutrition_entries = NutritionEntry.query.filter(
        NutritionEntry.date >= date(today.year, today.month, 1)
    ).all()
    
    calendar_data = {}
    
    # Dodaje wpisy sportowe
    for entry in sport_entries:
        date_str = entry.date.strftime('%Y-%m-%d')
        if date_str not in calendar_data:
            calendar_data[date_str] = []
        calendar_data[date_str].append({
            'type': 'sport',
            'activity': entry.activity,
            'duration': entry.duration,
            'id': entry.id
        })
    
    # Dodaje wpisy żywieniowe
    for entry in nutrition_entries:
        date_str = entry.date.strftime('%Y-%m-%d')
        if date_str not in calendar_data:
            calendar_data[date_str] = []
        calendar_data[date_str].append({
            'type': 'nutrition',
            'meal_type': entry.meal_type,
            'food_item': entry.food_item,
            'calories': entry.calories,
            'id': entry.id
        })
    
    return render_template('calendar.html', calendar_data=calendar_data)

@app.route('/day/<date_str>')
def day_details(date_str):
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Nieprawidłowa data!', 'error')
        return redirect(url_for('calendar'))
    
    # Pobiera wszystkie wpisy dla tego dnia
    sport_entries = SportEntry.query.filter(SportEntry.date == selected_date).all()
    nutrition_entries = NutritionEntry.query.filter(NutritionEntry.date == selected_date).all()
    personal_entries = PersonalData.query.filter(PersonalData.date == selected_date).all()
    
    return render_template('day_details.html', 
                         selected_date=selected_date,
                         sport_entries=sport_entries,
                         nutrition_entries=nutrition_entries,
                         personal_entries=personal_entries)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.jinja_env.globals['timedelta'] = timedelta
    
    app.run(debug=True, host='127.0.0.1', port=5001)
