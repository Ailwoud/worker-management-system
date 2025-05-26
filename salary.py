from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.salary import Salary
from src.models.employee import Employee
from datetime import datetime

salary_bp = Blueprint('salary', __name__)

@salary_bp.route('/', methods=['GET'])
def get_all_salaries():
    """الحصول على جميع سجلات الرواتب"""
    salaries = Salary.query.all()
    return jsonify({
        'status': 'success',
        'data': [salary.to_dict() for salary in salaries]
    }), 200

@salary_bp.route('/<int:id>', methods=['GET'])
def get_salary(id):
    """الحصول على سجل راتب محدد بواسطة المعرف"""
    salary = Salary.query.get_or_404(id)
    return jsonify({
        'status': 'success',
        'data': salary.to_dict()
    }), 200

@salary_bp.route('/employee/<int:employee_id>', methods=['GET'])
def get_employee_salaries(employee_id):
    """الحصول على جميع سجلات رواتب عامل محدد"""
    # التحقق من وجود العامل
    employee = Employee.query.get_or_404(employee_id)
    
    # الحصول على سجلات الرواتب
    salaries = Salary.query.filter_by(employee_id=employee_id).all()
    
    return jsonify({
        'status': 'success',
        'employee': employee.to_dict(),
        'data': [salary.to_dict() for salary in salaries]
    }), 200

@salary_bp.route('/', methods=['POST'])
def create_salary():
    """إنشاء سجل راتب جديد"""
    data = request.get_json()
    
    # التحقق من البيانات المطلوبة
    if not data.get('employee_id') or not data.get('amount') or not data.get('payment_date'):
        return jsonify({
            'status': 'error',
            'message': 'معرف العامل والمبلغ وتاريخ الدفع مطلوبة'
        }), 400
    
    # التحقق من وجود العامل
    employee = Employee.query.get(data.get('employee_id'))
    if not employee:
        return jsonify({
            'status': 'error',
            'message': 'العامل غير موجود'
        }), 404
    
    # تحويل تاريخ الدفع إلى كائن تاريخ
    try:
        payment_date = datetime.strptime(data.get('payment_date'), '%Y-%m-%d').date()
    except ValueError:
        return jsonify({
            'status': 'error',
            'message': 'صيغة تاريخ الدفع غير صحيحة. يجب أن تكون بصيغة YYYY-MM-DD'
        }), 400
    
    # إنشاء كائن الراتب
    salary = Salary(
        employee_id=data.get('employee_id'),
        amount=data.get('amount'),
        bonus=data.get('bonus', 0),
        deduction=data.get('deduction', 0),
        payment_date=payment_date,
        payment_method=data.get('payment_method', 'نقدي'),
        notes=data.get('notes'),
        status=data.get('status', 'مدفوع')
    )
    
    # حفظ في قاعدة البيانات
    db.session.add(salary)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم إنشاء سجل الراتب بنجاح',
        'data': salary.to_dict()
    }), 201

@salary_bp.route('/<int:id>', methods=['PUT'])
def update_salary(id):
    """تحديث سجل راتب محدد"""
    salary = Salary.query.get_or_404(id)
    data = request.get_json()
    
    # تحديث البيانات
    if 'amount' in data:
        salary.amount = data.get('amount')
    if 'bonus' in data:
        salary.bonus = data.get('bonus')
    if 'deduction' in data:
        salary.deduction = data.get('deduction')
    if 'payment_method' in data:
        salary.payment_method = data.get('payment_method')
    if 'notes' in data:
        salary.notes = data.get('notes')
    if 'status' in data:
        salary.status = data.get('status')
    
    # تحويل تاريخ الدفع إذا كان موجودًا
    if data.get('payment_date'):
        try:
            salary.payment_date = datetime.strptime(data.get('payment_date'), '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'صيغة تاريخ الدفع غير صحيحة. يجب أن تكون بصيغة YYYY-MM-DD'
            }), 400
    
    # تحديث تاريخ التعديل
    salary.updated_at = datetime.utcnow()
    
    # حفظ التغييرات
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم تحديث سجل الراتب بنجاح',
        'data': salary.to_dict()
    }), 200

@salary_bp.route('/<int:id>', methods=['DELETE'])
def delete_salary(id):
    """حذف سجل راتب محدد"""
    salary = Salary.query.get_or_404(id)
    
    # حذف سجل الراتب
    db.session.delete(salary)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم حذف سجل الراتب بنجاح'
    }), 200

@salary_bp.route('/report', methods=['GET'])
def salary_report():
    """تقرير الرواتب حسب الفترة"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status')
    
    # بناء الاستعلام
    query = Salary.query
    
    # تطبيق الفلاتر
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Salary.payment_date >= start)
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'صيغة تاريخ البداية غير صحيحة. يجب أن تكون بصيغة YYYY-MM-DD'
            }), 400
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Salary.payment_date <= end)
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'صيغة تاريخ النهاية غير صحيحة. يجب أن تكون بصيغة YYYY-MM-DD'
            }), 400
    
    if status:
        query = query.filter(Salary.status == status)
    
    # تنفيذ الاستعلام
    salaries = query.all()
    
    # حساب الإجماليات
    total_amount = sum(salary.amount for salary in salaries)
    total_bonus = sum(salary.bonus for salary in salaries)
    total_deduction = sum(salary.deduction for salary in salaries)
    net_amount = total_amount + total_bonus - total_deduction
    
    return jsonify({
        'status': 'success',
        'count': len(salaries),
        'summary': {
            'total_amount': total_amount,
            'total_bonus': total_bonus,
            'total_deduction': total_deduction,
            'net_amount': net_amount
        },
        'data': [salary.to_dict() for salary in salaries]
    }), 200
