from flask import Blueprint, request, jsonify
from src.models.user import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/', methods=['GET'])
def get_all_users():
    """الحصول على جميع المستخدمين"""
    users = User.query.all()
    return jsonify({
        'status': 'success',
        'data': [user.to_dict() for user in users]
    }), 200

@user_bp.route('/<int:id>', methods=['GET'])
def get_user(id):
    """الحصول على مستخدم محدد بواسطة المعرف"""
    user = User.query.get_or_404(id)
    return jsonify({
        'status': 'success',
        'data': user.to_dict()
    }), 200

@user_bp.route('/register', methods=['POST'])
def register_user():
    """تسجيل مستخدم جديد"""
    data = request.get_json()
    
    # التحقق من البيانات المطلوبة
    if not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({
            'status': 'error',
            'message': 'اسم المستخدم والبريد الإلكتروني وكلمة المرور مطلوبة'
        }), 400
    
    # التحقق من عدم وجود مستخدم بنفس اسم المستخدم أو البريد الإلكتروني
    if User.query.filter_by(username=data.get('username')).first():
        return jsonify({
            'status': 'error',
            'message': 'اسم المستخدم موجود بالفعل'
        }), 400
    
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({
            'status': 'error',
            'message': 'البريد الإلكتروني موجود بالفعل'
        }), 400
    
    # إنشاء كائن المستخدم
    user = User(
        username=data.get('username'),
        email=data.get('email'),
        password=generate_password_hash(data.get('password')),
        role=data.get('role', 'عامل'),
        employee_id=data.get('employee_id')
    )
    
    # حفظ في قاعدة البيانات
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم تسجيل المستخدم بنجاح',
        'data': user.to_dict()
    }), 201

@user_bp.route('/login', methods=['POST'])
def login_user():
    """تسجيل دخول المستخدم"""
    data = request.get_json()
    
    # التحقق من البيانات المطلوبة
    if not data.get('username') or not data.get('password'):
        return jsonify({
            'status': 'error',
            'message': 'اسم المستخدم وكلمة المرور مطلوبة'
        }), 400
    
    # البحث عن المستخدم
    user = User.query.filter_by(username=data.get('username')).first()
    
    # التحقق من وجود المستخدم وصحة كلمة المرور
    if not user or not check_password_hash(user.password, data.get('password')):
        return jsonify({
            'status': 'error',
            'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'
        }), 401
    
    # تحديث آخر تسجيل دخول
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم تسجيل الدخول بنجاح',
        'data': user.to_dict()
    }), 200

@user_bp.route('/<int:id>', methods=['PUT'])
def update_user(id):
    """تحديث بيانات مستخدم محدد"""
    user = User.query.get_or_404(id)
    data = request.get_json()
    
    # تحديث البيانات
    if data.get('username'):
        # التحقق من عدم وجود مستخدم آخر بنفس اسم المستخدم
        existing_user = User.query.filter_by(username=data.get('username')).first()
        if existing_user and existing_user.id != id:
            return jsonify({
                'status': 'error',
                'message': 'اسم المستخدم موجود بالفعل'
            }), 400
        user.username = data.get('username')
    
    if data.get('email'):
        # التحقق من عدم وجود مستخدم آخر بنفس البريد الإلكتروني
        existing_user = User.query.filter_by(email=data.get('email')).first()
        if existing_user and existing_user.id != id:
            return jsonify({
                'status': 'error',
                'message': 'البريد الإلكتروني موجود بالفعل'
            }), 400
        user.email = data.get('email')
    
    if data.get('password'):
        user.password = generate_password_hash(data.get('password'))
    
    if 'role' in data:
        user.role = data.get('role')
    
    if 'employee_id' in data:
        user.employee_id = data.get('employee_id')
    
    # حفظ التغييرات
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم تحديث بيانات المستخدم بنجاح',
        'data': user.to_dict()
    }), 200

@user_bp.route('/<int:id>', methods=['DELETE'])
def delete_user(id):
    """حذف مستخدم محدد"""
    user = User.query.get_or_404(id)
    
    # حذف المستخدم
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'تم حذف المستخدم بنجاح'
    }), 200
