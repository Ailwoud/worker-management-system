from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.attendance import Attendance
from src.models.employee import Employee
from datetime import datetime, timedelta

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/', methods=['GET'])
def get_all_attendance():
    """الحصول على جميع سجلات الحضور"""
    attendance_records = Attendance.query.all()
    return jsonify({
        'status': 'success',
        'data': [record.to_dict() for record in attendance_records]
    }), 200

@attendance_bp.route('/<int:id>', methods=['GET'])
def get_attendance(id):
    """الحصول على سجل حضور محدد بواسطة المعرف"""
    attendance = Attendance.query.get_or_404(id)
    return jsonify({
        'status': 'success',
        'data': attendance.to_dict()
    }), 200

@attendance_bp.route('/employee/<int:employee_id>', methods=['GET'])
def get_employee_attendance(employee_id):
    """الحصول على جميع سجلات حضور عامل محدد"""
    # التحقق من وجود العامل
    employee = Employee.query.get_or_404(employee_id)
    
    # الحصول على سجلات الحضور
    attendance_records = Attendance.query.filter_by(employee_id=employee_id).all()
    
    return jsonify({
        'status': 'success',
        'employee': employee.to_dict(),
        'data': [record.to_dict() for record in attendance_records]
    }), 200

@attendance_bp.route('/check-in', methods=['POST'])
def check_in():
    """تسجيل دخول عامل"""
    data = request.get_json()
    
    # التحقق من البيانات المطلوبة
    if not data.get('employee_id'):
        return jsonify({
            'status': 'error',
            'message': 'معرف العامل مطلوب'
        }), 400
    
    # التحقق من وجود العامل
    employee = Employee.query.get(data.get('employee_id'))
    if not employee:
        return jsonify({
            'status': 'error',
            'message': 'العامل غير موجود'
        }), 404
    
    # التحقق من عدم وجود تسجيل دخول سابق في نفس اليوم
    today = datetime.utcnow().date()
    existing_record = Attendance.query.filter_by(
        employee_id=data.get('employee_id'),
        date=today
    ).first()
    
    if existing_record:
        if existing_record.check_in:
            return jsonify({
                'status': 'error',
                'message': 'تم تسجيل دخول العامل مسبقًا اليوم',
                'data': existing_record.to_dict()
            }), 400
        else:
            # تحديث سجل موجود
            existing_record.check_in = datetime.utcnow()
            existing_record.status = 'حاضر'
            db.session.commit()
            return jsonify({
                'status': 'success',
                'message': 'تم تسجيل دخول العامل بنجاح',
                'data': existing_record.to_dict()
            }), 200
    
    # إنشاء سجل حضور جديد
    attendance = Attendance(
        employee_id=data.get('employee_id'),
        check_in=datetime.utcnow(),
        date=today,
        status='حاضر',
        notes=data.get('notes')
    )
    
    # حفظ في قاعدة البيانات
    db.session.add(attendance)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم تسجيل دخول العامل بنجاح',
        'data': attendance.to_dict()
    }), 201

@attendance_bp.route('/check-out', methods=['PUT'])
def check_out():
    """تسجيل خروج عامل"""
    data = request.get_json()
    
    # التحقق من البيانات المطلوبة
    if not data.get('employee_id'):
        return jsonify({
            'status': 'error',
            'message': 'معرف العامل مطلوب'
        }), 400
    
    # التحقق من وجود العامل
    employee = Employee.query.get(data.get('employee_id'))
    if not employee:
        return jsonify({
            'status': 'error',
            'message': 'العامل غير موجود'
        }), 404
    
    # البحث عن سجل الحضور لليوم الحالي
    today = datetime.utcnow().date()
    attendance = Attendance.query.filter_by(
        employee_id=data.get('employee_id'),
        date=today
    ).first()
    
    if not attendance:
        return jsonify({
            'status': 'error',
            'message': 'لم يتم تسجيل دخول العامل اليوم'
        }), 404
    
    if attendance.check_out:
        return jsonify({
            'status': 'error',
            'message': 'تم تسجيل خروج العامل مسبقًا اليوم',
            'data': attendance.to_dict()
        }), 400
    
    # تحديث سجل الحضور
    attendance.check_out = datetime.utcnow()
    
    # حساب ساعات العمل
    if attendance.check_in:
        time_diff = attendance.check_out - attendance.check_in
        attendance.working_hours = time_diff.total_seconds() / 3600  # تحويل إلى ساعات
    
    # إضافة ملاحظات إذا وجدت
    if data.get('notes'):
        attendance.notes = data.get('notes')
    
    # حفظ التغييرات
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم تسجيل خروج العامل بنجاح',
        'data': attendance.to_dict()
    }), 200

@attendance_bp.route('/<int:id>', methods=['PUT'])
def update_attendance(id):
    """تحديث سجل حضور محدد"""
    attendance = Attendance.query.get_or_404(id)
    data = request.get_json()
    
    # تحديث البيانات
    if 'status' in data:
        attendance.status = data.get('status')
    if 'notes' in data:
        attendance.notes = data.get('notes')
    
    # تحويل تواريخ الدخول والخروج إذا كانت موجودة
    if data.get('check_in'):
        try:
            attendance.check_in = datetime.strptime(data.get('check_in'), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'صيغة وقت الدخول غير صحيحة. يجب أن تكون بصيغة YYYY-MM-DD HH:MM:SS'
            }), 400
    
    if data.get('check_out'):
        try:
            attendance.check_out = datetime.strptime(data.get('check_out'), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'صيغة وقت الخروج غير صحيحة. يجب أن تكون بصيغة YYYY-MM-DD HH:MM:SS'
            }), 400
    
    # تحديث ساعات العمل إذا كان هناك وقت دخول وخروج
    if attendance.check_in and attendance.check_out:
        time_diff = attendance.check_out - attendance.check_in
        attendance.working_hours = time_diff.total_seconds() / 3600
    
    # تحديث تاريخ التعديل
    attendance.updated_at = datetime.utcnow()
    
    # حفظ التغييرات
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم تحديث سجل الحضور بنجاح',
        'data': attendance.to_dict()
    }), 200

@attendance_bp.route('/<int:id>', methods=['DELETE'])
def delete_attendance(id):
    """حذف سجل حضور محدد"""
    attendance = Attendance.query.get_or_404(id)
    
    # حذف سجل الحضور
    db.session.delete(attendance)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم حذف سجل الحضور بنجاح'
    }), 200

@attendance_bp.route('/report', methods=['GET'])
def attendance_report():
    """تقرير الحضور حسب الفترة"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    employee_id = request.args.get('employee_id')
    status = request.args.get('status')
    
    # بناء الاستعلام
    query = Attendance.query
    
    # تطبيق الفلاتر
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.date >= start)
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'صيغة تاريخ البداية غير صحيحة. يجب أن تكون بصيغة YYYY-MM-DD'
            }), 400
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.date <= end)
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'صيغة تاريخ النهاية غير صحيحة. يجب أن تكون بصيغة YYYY-MM-DD'
            }), 400
    
    if employee_id:
        query = query.filter(Attendance.employee_id == employee_id)
    
    if status:
        query = query.filter(Attendance.status == status)
    
    # تنفيذ الاستعلام
    attendance_records = query.all()
    
    # حساب الإحصائيات
    total_hours = sum(record.working_hours or 0 for record in attendance_records)
    present_count = sum(1 for record in attendance_records if record.status == 'حاضر')
    absent_count = sum(1 for record in attendance_records if record.status == 'غائب')
    late_count = sum(1 for record in attendance_records if record.status == 'متأخر')
    
    return jsonify({
        'status': 'success',
        'count': len(attendance_records),
        'summary': {
            'total_hours': total_hours,
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count
        },
        'data': [record.to_dict() for record in attendance_records]
    }), 200
