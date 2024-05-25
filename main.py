from quart import Quart, request, jsonify
import json
from t_mobile_checker import TMobileChecker

app = Quart(__name__)
checker = TMobileChecker()

@app.route('/check')
async def check():
    imei = request.args.get('imei')
    if imei:
        result = await checker.main(imei)
        return jsonify(json.loads(result))
    else:
        return jsonify({"error": "IMEI parameter is missing"}), 400

if __name__ == '__main__':
    app.run()
