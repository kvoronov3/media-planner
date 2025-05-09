import sys
import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models import db, User, MediaPlan, Platform, MediaPlanPlatform
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import csv
from io import StringIO, BytesIO

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres.vairruppstiiqvqvcjej:Qwerty#321@aws-0-eu-west-2.pooler.supabase.com:6543/postgres')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, User):
    pass

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        user = User.query.filter_by(login=login).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверный логин или пароль')
    return render_template('login.html')

@app.route('/')
@login_required
def index():
    plans = MediaPlan.query.filter_by(user_id=current_user.id).all()
    total_budget = sum(plan.budget for plan in plans) if plans else 0
    total_impressions = sum(sum(platform.impressions for platform in plan.platforms) for plan in plans) if plans else 0
    return render_template('index.html', total_budget=total_budget, total_impressions=total_impressions, plans=plans)

@app.route('/edit_plan/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def edit_plan(plan_id):
    plan = MediaPlan.query.get_or_404(plan_id)
    if plan.user_id != current_user.id:
        flash('У вас нет прав на редактирование этого медиаплана')
        return redirect(url_for('index'))
    platforms = Platform.query.all()
    campaign_cycles = ['Рост', 'Зрелость', 'Спад', 'Запуск']
    if request.method == 'POST':
        plan.name = request.form['name']
        plan.budget = float(request.form['budget'])
        plan.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        plan.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        plan.target_audience = request.form['target_audience']
        plan.campaign_cycle = request.form['campaign_cycle']
        db.session.commit()
        flash('Медиаплан успешно обновлен!')
        return redirect(url_for('index'))
    return render_template('edit_plan.html', plan=plan, platforms=platforms, campaign_cycles=campaign_cycles)

@app.route('/delete_plan/<int:plan_id>', methods=['POST'])
@login_required
def delete_plan(plan_id):
    plan = MediaPlan.query.get_or_404(plan_id)
    if plan.user_id != current_user.id:
        flash('У вас нет прав на удаление этого медиаплана')
        return redirect(url_for('index'))
    db.session.delete(plan)
    db.session.commit()
    flash('Медиаплан успешно удален!')
    return redirect(url_for('index'))

@app.route('/create_plan_traditional', methods=['GET', 'POST'])
@login_required
def create_plan_traditional():
    platforms = Platform.query.all()
    campaign_cycles = ['Рост', 'Зрелость', 'Спад', 'Запуск']
    if request.method == 'POST':
        name = request.form['name']
        budget = float(request.form['budget'])
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        target_audience = request.form['target_audience']
        campaign_cycle = request.form['campaign_cycle']

        if budget <= 0:
            flash('Бюджет должен быть больше 0')
            return redirect(url_for('create_plan_traditional'))

        new_plan = MediaPlan(
            user_id=current_user.id,
            name=name,
            budget=budget,
            start_date=start_date,
            end_date=end_date,
            target_audience=target_audience,
            campaign_cycle=campaign_cycle
        )
        db.session.add(new_plan)
        db.session.commit()

        total_platform_budget = 0
        for platform in platforms:
            platform_id = platform.id
            platform_budget = float(request.form[f'platform_budget_{platform_id}'])
            if platform_budget > 0:
                total_platform_budget += platform_budget
                media_plan_platform = MediaPlanPlatform(
                    media_plan_id=new_plan.id,
                    platform_id=platform_id,
                    budget=platform_budget
                )
                db.session.add(media_plan_platform)
        db.session.commit()

        if total_platform_budget != budget:
            flash('Сумма бюджетов по платформам должна совпадать с общим бюджетом')
            db.session.delete(new_plan)
            db.session.commit()
            return redirect(url_for('create_plan_traditional'))

        flash('Медиаплан успешно создан!')
        return redirect(url_for('index'))
    return render_template('create_plan_traditional.html', platforms=platforms, campaign_cycles=campaign_cycles)

@app.route('/create_plan_innovative', methods=['GET', 'POST'])
@login_required
def create_plan_innovative():
    platforms = Platform.query.all()
    campaign_cycles = ['Рост', 'Зрелость', 'Спад', 'Запуск']
    if request.method == 'POST':
        name = request.form['name']
        budget = float(request.form['budget'])
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        target_audience = request.form['target_audience']
        campaign_cycle = request.form['campaign_cycle']

        if budget <= 0:
            flash('Бюджет должен быть больше 0')
            return redirect(url_for('create_plan_innovative'))

        new_plan = MediaPlan(
            user_id=current_user.id,
            name=name,
            budget=budget,
            start_date=start_date,
            end_date=end_date,
            target_audience=target_audience,
            campaign_cycle=campaign_cycle
        )
        db.session.add(new_plan)
        db.session.commit()

        total_platform_budget = 0
        cycle_weights = {
            'Рост': {'Facebook': 0.4, 'Instagram': 0.3, 'YouTube': 0.2, 'Telegram': 0.1},
            'Зрелость': {'Facebook': 0.25, 'Instagram': 0.25, 'YouTube': 0.25, 'Telegram': 0.25},
            'Спад': {'Facebook': 0.2, 'Instagram': 0.2, 'YouTube': 0.2, 'Telegram': 0.4},
            'Запуск': {'Facebook': 0.5, 'Instagram': 0.3, 'YouTube': 0.15, 'Telegram': 0.05}
        }
        weights = cycle_weights.get(campaign_cycle, {'Facebook': 0.25, 'Instagram': 0.25, 'YouTube': 0.25, 'Telegram': 0.25})
        
        for platform in platforms:
            platform_id = platform.id
            platform_weight = weights.get(platform.name, 0.25)
            platform_budget = budget * platform_weight
            if platform_budget > 0:
                total_platform_budget += platform_budget
                media_plan_platform = MediaPlanPlatform(
                    media_plan_id=new_plan.id,
                    platform_id=platform_id,
                    budget=platform_budget
                )
                db.session.add(media_plan_platform)
        db.session.commit()

        flash('Медиаплан успешно создан с учётом инновационного подхода!')
        return redirect(url_for('index'))
    return render_template('create_plan_innovative.html', platforms=platforms, campaign_cycles=campaign_cycles)

@app.route('/suggest-budget', methods=['POST'])
@login_required
def suggest_budget():
    total_budget = float(request.form['total_budget'])
    platforms = Platform.query.all()
    total_ctr = sum(platform.average_ctr for platform in platforms)
    if total_ctr == 0:
        distribution = {platform.name: total_budget / len(platforms) for platform in platforms}
    else:
        distribution = {platform.name: (platform.average_ctr / total_ctr) * total_budget for platform in platforms}
    return jsonify(distribution)

@app.route('/analysis', methods=['GET', 'POST'])
@login_required
def analysis():
    status_filter = request.args.get('status', 'all')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    query = MediaPlan.query.filter_by(user_id=current_user.id)
    if status_filter == 'active':
        query = query.filter(MediaPlan.end_date >= datetime.today().date())
    elif status_filter == 'completed':
        query = query.filter(MediaPlan.end_date < datetime.today().date())
    if date_from:
        query = query.filter(MediaPlan.start_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        query = query.filter(MediaPlan.end_date <= datetime.strptime(date_to, '%Y-%m-%d').date())

    page = request.args.get('page', 1, type=int)
    per_page = 10
    plans_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    plans = plans_paginated.items

    selected_plans = []
    compare_data = None

    if request.method == 'POST':
        selected_plan_ids = request.form.getlist('plans')
        selected_plan_ids = [int(plan_id) for plan_id in selected_plan_ids]
        selected_plans = MediaPlan.query.filter(MediaPlan.id.in_(selected_plan_ids)).all()

        compare_data = []
        for plan in selected_plans:
            plan_data = {
                'name': plan.name,
                'budget': plan.budget,
                'ctr': 0,
                'platforms': []
            }
            total_impressions = 0
            total_clicks = 0
            for platform in plan.platforms:
                impressions = platform.impressions if platform.impressions is not None else 0
                clicks = platform.clicks if platform.clicks is not None else 0
                total_impressions += impressions
                total_clicks += clicks
                platform_data = {
                    'name': platform.platform.name,
                    'ctr': (clicks / impressions * 100) if impressions > 0 else 0
                }
                plan_data['platforms'].append(platform_data)
            plan_data['ctr'] = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
            compare_data.append(plan_data)

    recommendations = []
    for plan in plans:
        for platform in plan.platforms:
            platform.clicks = platform.clicks if platform.clicks is not None else 0
            platform.impressions = platform.impressions if platform.impressions is not None else 0
            platform.forecasted_impressions = int((platform.budget / 500) * 1000)
            platform.forecasted_clicks = int(platform.forecasted_impressions * (platform.platform.average_ctr / 100))
            platform.ctr = (platform.clicks / platform.impressions * 100) if platform.impressions > 0 else 0
            platform.cpc = platform.budget / platform.clicks if platform.clicks > 0 else 0
            platform.cpm = (platform.budget / (platform.impressions / 1000)) if platform.impressions > 0 else 0

            if platform.ctr > 5:
                recommendations.append(f"Увеличьте бюджет на {platform.platform.name} в медиаплане {plan.name}, так как CTR ({platform.ctr:.2f}%) выше среднего.")
            if platform.cpm > 1000:
                recommendations.append(f"Снизьте бюджет на {platform.platform.name} в медиаплане {plan.name}, так как CPM ({platform.cpm:.2f} ₽) слишком высокий.")

    return render_template('analysis.html', plans=plans, selected_plans=selected_plans, compare_data=compare_data, plans_paginated=plans_paginated, recommendations=recommendations)

@app.route('/reports', methods=['GET', 'POST'])
@login_required
def reports():
    today = datetime.today().date()
    date_ranges = {
        'last_7_days': {
            'start': (today - timedelta(days=7)).strftime('%Y-%m-%d'),
            'end': today.strftime('%Y-%m-%d'),
            'label': 'Последние 7 дней'
        },
        'last_30_days': {
            'start': (today - timedelta(days=30)).strftime('%Y-%m-%d'),
            'end': today.strftime('%Y-%m-%d'),
            'label': 'Последние 30 дней'
        },
        'current_month': {
            'start': (today.replace(day=1)).strftime('%Y-%m-%d'),
            'end': today.strftime('%Y-%m-%d'),
            'label': 'Текущий месяц'
        },
        'last_month': {
            'start': (today.replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m-%d'),
            'end': (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d'),
            'label': 'Прошлый месяц'
        }
    }

    if request.method == 'POST':
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        plans = MediaPlan.query.filter_by(user_id=current_user.id).filter(
            MediaPlan.start_date >= start_date, MediaPlan.end_date <= end_date
        ).all()

        if 'preview' in request.form:
            plans_data = []
            for plan in plans:
                plan_data = {
                    'name': plan.name,
                    'budget': plan.budget,
                    'start_date': plan.start_date.strftime('%Y-%m-%d'),
                    'end_date': plan.end_date.strftime('%Y-%m-%d'),
                    'target_audience': plan.target_audience,
                    'campaign_cycle': plan.campaign_cycle,
                    'platforms': [
                        {
                            'platform_name': platform.platform.name,
                            'budget': platform.budget,
                            'impressions': platform.impressions,
                            'clicks': platform.clicks,
                            'forecasted_impressions': platform.forecasted_impressions,
                            'forecasted_clicks': platform.forecasted_clicks
                        } for platform in plan.platforms
                    ]
                }
                plans_data.append(plan_data)
            return jsonify({'plans': plans_data})

        if not plans:
            flash('Нет медиапланов для выбранного периода.')
            return redirect(url_for('reports'))

        pdf_filename = f"report_{start_date}_{end_date}.pdf"
        c = canvas.Canvas(pdf_filename, pagesize=letter)
        c.setFont("Helvetica", 12)
        c.drawString(100, 750, "Отчет по медиапланам")
        c.drawString(100, 730, f"Период: {start_date} - {end_date}")
        y = 700
        for plan in plans:
            c.drawString(100, y, f"Медиаплан: {plan.name}")
            y -= 20
            c.drawString(100, y, f"Бюджет: {plan.budget} ₽")
            y -= 20
            c.drawString(100, y, f"Даты: {plan.start_date} - {plan.end_date}")
            y -= 20
            c.drawString(100, y, f"Целевая аудитория: {plan.target_audience}")
            y -= 20
            c.drawString(100, y, f"Цикл кампании: {plan.campaign_cycle}")
            y -= 20
            c.drawString(100, y, "Платформы:")
            y -= 20
            for platform in plan.platforms:
                c.drawString(120, y, f"{platform.platform.name}: {platform.budget} ₽")
                y -= 20
                c.drawString(120, y, f"Показы: {platform.impressions}, Клики: {platform.clicks}")
                y -= 20
                c.drawString(120, y, f"Ожидаемые показы: {platform.forecasted_impressions}, Ожидаемые клики: {platform.forecasted_clicks}")
                y -= 20
                if y < 50:
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y = 750
        c.save()
        return send_file(pdf_filename, as_attachment=True)
    
    return render_template('reports.html', date_ranges=date_ranges)

@app.route('/export_plans', methods=['GET'])
@login_required
def export_plans():
    plans = MediaPlan.query.filter_by(user_id=current_user.id).all()
    # Сначала создаем CSV в текстовом формате с помощью StringIO
    output = StringIO()
    writer = csv.writer(output, lineterminator='\n')  # Используем lineterminator для корректных переносов строк
    writer.writerow(['ID', 'Название', 'Бюджет', 'Дата начала', 'Дата окончания', 'Целевая аудитория', 'Цикл кампании', 'Платформы'])
    for plan in plans:
        platforms_info = "; ".join([f"{p.platform.name}: {p.budget} ₽, Показы: {p.impressions}, Клики: {p.clicks}" for p in plan.platforms])
        writer.writerow([plan.id, plan.name, plan.budget, plan.start_date, plan.end_date, plan.target_audience, plan.campaign_cycle, platforms_info])
    
    # Преобразуем содержимое StringIO в BytesIO с кодировкой UTF-8
    output.seek(0)
    bytes_output = BytesIO(output.getvalue().encode('utf-8'))
    output.close()  # Закрываем StringIO

    return send_file(
        bytes_output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='media_plans.csv'
    )

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)