from flask import jsonify
def success(data=None): return jsonify({'code':0,'data':data})
def error(msg): return jsonify({'code':1,'msg':msg})
