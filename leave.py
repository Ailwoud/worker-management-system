from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.leave import Leave
from src.models.employee import Employee
from datetime import datetime

leave_bp = Blueprint('leave', __name__)

@leave_bp.route('/', methods=['GET'])
def get_all_leaves():
    """الحصول على جميع سجلات الإجازات"""
    leaves = Leave.query.all()
    return jsonify({
        'status': 'success',
        'data': [leave.to_dict() for leave in leaves]
    }), 200

@leave_bp.route('/<int:id>', methods=['GET'])
def get_leave(id):
    """الحصول على سجل إجازة محدد بواسطة المعرف"""
    leave = Leave.query.get_or_404(id)
    return jsonify({
        'status': 'success',
        'data': leave.to_dict()
    }), 200

@leave_bp.route('/employee/<int:employee_id>', methods=['GET'])
def get_employee_leaves(employee_id):
    """الحصول على جميع سجلات إجازات عامل محدد"""
    # التحقق من وجود العامل
    employee = Employee.query.get_or_404(employee_id)
    
    # الحصول على سجلات الإجازات
    leaves = Leave.query.filter_by(employee_id=employee_id).all()
    
    return jsonify({
        'status': 'success',
        'employee': employee.to_dict(),
        'data': [leave.to_dict() for leave in leaves]
    }), 200

@leave_bp.route('/', methods=['POST'])
def create_leave():
    """إنشاء طلب إجازة جديد"""
    data = request.get_json()
    
    # التحقق من البيانات المطلوبة
    if not data.get('employee_id') or not data.get('start_date') or not data.get('end_date') or not data.get('leave_type'):
        return jsonify({
            'status': 'error',
            'message': 'معرف العامل وتاريخ البداية والنهاية ونوع الإجازة مطلوبة'
        }), 400
    
    # التحقق من وجود العامل
    employee = Employee.query.get(data.get('employee_id'))
    if not employee:
        return jsonify({
            'status': 'error',
            'message': 'العامل غير موجود'
        }), 404
    
    # تحويل تواريخ الإجازة إلى كائنات تاريخ
    try:
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
    except ValueError:
        return jsonify({
            'status': 'error',
            'message': 'صيغة التاريخ غير صحيحة. يجب أن تكون بصيغة YYYY-MM-DD'
        }), 400
    
    # التحقق من صحة التواريخ
    if start_date > end_date:
        return jsonify({
            'status': 'error',
            'message': 'تاريخ البداية يجب أن يكون قبل تاريخ النهاية'
        }), 400
    
    # إنشاء كائن الإجازة
    leave = Leave(
        employee_id=data.get('employee_id'),
        start_date=start_date,
        end_date=end_date,
        leave_type=data.get('leave_type'),
        reason=data.get('reason'),
        status=data.get('status', 'معلق'),
        approved_by=data.get('approved_by')
    )
    
    # حفظ في قاعدة البيانات
    db.session.add(leave)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم إنشاء طلب الإجازة بنجاح',
        'data': leave.to_dict()
    }), 201

@leave_bp.route('/<int:id>', methods=['PUT'])
def update_leave(id):
    """تحديث سجل إجازة محدد"""
    leave = Leave.query.get_or_404(id)
    data = request.get_json()
    
    # تحديث البيانات
    if 'leave_type' in data:
        leave.leave_type = data.get('leave_type')
    if 'reason' in data:
        leave.reason = data.get('reason')
    if 'status' in data:
        leave.status = data.get('status')
    if 'approved_by' in data:
        leave.approved_by = data.get('approved_by')
    
    # تحويل تواريخ الإجازة إذا كانت موجودة
    if data.get('start_date'):
        try:
            leave.start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'صيغة تاريخ البداية غير صحيحة. يجب أن تكون بصيغة YYYY-MM-DD'
            }), 400
    
    if data.get('end_date'):
        try:
            leave.end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'صيغة تاريخ النهاية غير صحيحة. يجب أن تكون بصيغة YYYY-MM-DD'
            }), 400
    
    # التحقق من صحة التواريخ
    if leave.start_date > leave.end_date:
        return jsonify({
            'status': 'error',
            'message': 'تاريخ البداية يجب أن يكون قبل تاريخ النهاية'
        }), 400
    
    # تحديث تاريخ التعديل
    leave.updated_at = datetime.utcnow()
    
    # حفظ التغييرات
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم تحديث سجل الإجازة بنجاح',
        'data': leave.to_dict()
    }), 200

@leave_bp.route('/<int:id>', methods=['DELETE'])
def delete_leave(id):
    """حذف سجل إجازة محدد"""
    leave = Leave.query.get_or_404(id)
    
    # حذف سجل الإجازة
    db.session.delete(leave)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم حذف سجل الإجازة بنجاح'
    }), 200

@leave_bp.route('/approve/<int:id>', methods=['PUT'])
def approve_leave(id):
    """الموافقة على طلب إجازة"""
    leave = Leave.query.get_or_404(id)
    data = request.get_json()
    
    # تحديث حالة الإجازة
    leave.status = 'موافق'
    if data.get('approved_by'):
        leave.approved_by = data.get('approved_by')
    
    # تحديث تاريخ التعديل
    leave.updated_at = datetime.utcnow()
    
    # حفظ التغييرات
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تمت الموافقة على طلب الإجازة بنجاح',
        'data': leave.to_dict()
    }), 200

@leave_bp.route('/reject/<int:id>', methods=['PUT'])
def reject_leave(id):
    """رفض طلب إجازة"""
    leave = Leave.query.get_or_404(id)
    data = request.get_json()
    
    # تحديث حالة الإجازة
    leave.status = 'مرفوض'
    if data.get('approved_by'):
        leave.approved_by = data.get('approved_by')
    
    # تحديث تاريخ التعديل
    leave.updated_at = datetime.utcnow()
    
    # حفظ التغييرات
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم رفض طلب الإجازة',
        'data': leave.to_dict()
    }), 200
