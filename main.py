from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from src.models.user import db
from src.models.employee import Employee
from src.models.salary import Salary
from src.models.leave import Leave
from src.models.attendance import Attendance
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template('index.html')

@main_bp.route('/dashboard')
def dashboard():
    """لوحة التحكم"""
    # إحصائيات سريعة
    employees_count = Employee.query.count()
    active_employees = Employee.query.filter_by(status='نشط').count()
    
    # آخر الرواتب المدفوعة
    recent_salaries = Salary.query.order_by(Salary.payment_date.desc()).limit(5).all()
    
    # طلبات الإجازات المعلقة
    pending_leaves = Leave.query.filter_by(status='معلق').count()
    
    # سجلات الحضور اليوم
    today = datetime.utcnow().date()
    today_attendance = Attendance.query.filter_by(date=today).count()
    
    return render_template('dashboard.html', 
                          employees_count=employees_count,
                          active_employees=active_employees,
                          recent_salaries=recent_salaries,
                          pending_leaves=pending_leaves,
                          today_attendance=today_attendance)

@main_bp.route('/employees')
def employees():
    """صفحة إدارة العمال"""
    employees_list = Employee.query.all()
    return render_template('employees.html', employees=employees_list)

@main_bp.route('/salaries')
def salaries():
    """صفحة إدارة الرواتب"""
    salaries_list = Salary.query.all()
    employees_list = Employee.query.all()
    return render_template('salaries.html', salaries=salaries_list, employees=employees_list)

@main_bp.route('/leaves')
def leaves():
    """صفحة إدارة الإجازات"""
    leaves_list = Leave.query.all()
    employees_list = Employee.query.all()
    return render_template('leaves.html', leaves=leaves_list, employees=employees_list)

@main_bp.route('/attendance')
def attendance():
    """صفحة إدارة الحضور"""
    attendance_list = Attendance.query.all()
    employees_list = Employee.query.all()
    return render_template('attendance.html', attendance=attendance_list, employees=employees_list)

@main_bp.route('/reports')
def reports():
    """صفحة التقارير"""
    return render_template('reports.html')

@main_bp.route('/profile')
def profile():
    """صفحة الملف الشخصي"""
    return render_template('profile.html')

@main_bp.route('/settings')
def settings():
    """صفحة الإعدادات"""
    return render_template('settings.html')
