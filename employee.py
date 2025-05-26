from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.employee import Employee
from datetime import datetime

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/', methods=['GET'])
def get_all_employees():
    """الحصول على جميع العمال"""
    employees = Employee.query.all()
    return jsonify({
        'status': 'success',
        'data': [employee.to_dict() for employee in employees]
    }), 200

@employee_bp.route('/<int:id>', methods=['GET'])
def get_employee(id):
    """الحصول على عامل محدد بواسطة المعرف"""
    employee = Employee.query.get_or_404(id)
    return jsonify({
        'status': 'success',
        'data': employee.to_dict()
    }), 200

@employee_bp.route('/', methods=['POST'])
def create_employee():
    """إنشاء عامل جديد"""
    data = request.get_json()
    
    # التحقق من البيانات المطلوبة
    if not data.get('first_name') or not data.get('last_name'):
        return jsonify({
            'status': 'error',
            'message': 'الاسم الأول والأخير مطلوبان'
        }), 400
    
    # تحويل تاريخ التوظيف إلى كائن تاريخ إذا كان موجودًا
    hire_date = None
    if data.get('hire_date'):
        try:
            hire_date = datetime.strptime(data.get('hire_date'), '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'صيغة تاريخ التوظيف غير صحيحة. يجب أن تكون بصيغة YYYY-MM-DD'
            }), 400
    
    # إنشاء كائن العامل
    employee = Employee(
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        phone=data.get('phone'),
        email=data.get('email'),
        address=data.get('address'),
        position=data.get('position'),
        department=data.get('department'),
        hire_date=hire_date,
        salary=data.get('salary'),
        status=data.get('status', 'نشط')
    )
    
    # حفظ في قاعدة البيانات
    db.session.add(employee)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم إنشاء العامل بنجاح',
        'data': employee.to_dict()
    }), 201

@employee_bp.route('/<int:id>', methods=['PUT'])
def update_employee(id):
    """تحديث بيانات عامل محدد"""
    employee = Employee.query.get_or_404(id)
    data = request.get_json()
    
    # تحديث البيانات
    if data.get('first_name'):
        employee.first_name = data.get('first_name')
    if data.get('last_name'):
        employee.last_name = data.get('last_name')
    if 'phone' in data:
        employee.phone = data.get('phone')
    if 'email' in data:
        employee.email = data.get('email')
    if 'address' in data:
        employee.address = data.get('address')
    if 'position' in data:
        employee.position = data.get('position')
    if 'department' in data:
        employee.department = data.get('department')
    if 'salary' in data:
        employee.salary = data.get('salary')
    if 'status' in data:
        employee.status = data.get('status')
    
    # تحويل تاريخ التوظيف إذا كان موجودًا
    if data.get('hire_date'):
        try:
            employee.hire_date = datetime.strptime(data.get('hire_date'), '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'صيغة تاريخ التوظيف غير صحيحة. يجب أن تكون بصيغة YYYY-MM-DD'
            }), 400
    
    # تحديث تاريخ التعديل
    employee.updated_at = datetime.utcnow()
    
    # حفظ التغييرات
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم تحديث بيانات العامل بنجاح',
        'data': employee.to_dict()
    }), 200

@employee_bp.route('/<int:id>', methods=['DELETE'])
def delete_employee(id):
    """حذف عامل محدد"""
    employee = Employee.query.get_or_404(id)
    
    # حذف العامل
    db.session.delete(employee)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم حذف العامل بنجاح'
    }), 200

@employee_bp.route('/search', methods=['GET'])
def search_employees():
    """البحث عن العمال بناءً على معايير مختلفة"""
    name = request.args.get('name')
    department = request.args.get('department')
    position = request.args.get('position')
    status = request.args.get('status')
    
    # بناء الاستعلام
    query = Employee.query
    
    if name:
        query = query.filter(
            (Employee.first_name.ilike(f'%{name}%')) | 
            (Employee.last_name.ilike(f'%{name}%'))
        )
    
    if department:
        query = query.filter(Employee.department.ilike(f'%{department}%'))
    
    if position:
        query = query.filter(Employee.position.ilike(f'%{position}%'))
    
    if status:
        query = query.filter(Employee.status == status)
    
    # تنفيذ الاستعلام
    employees = query.all()
    
    return jsonify({
        'status': 'success',
        'count': len(employees),
        'data': [employee.to_dict() for employee in employees]
    }), 200
