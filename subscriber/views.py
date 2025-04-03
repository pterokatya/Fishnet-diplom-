from rest_framework.decorators import api_view
from rest_framework.response import Response
import subprocess
import sys
import os

@api_view(['POST'])
def run_parser(request):
    user_input = request.data.get('query')  # например: "Рыночная 67" или "15762"

    if not user_input:
        return Response({'error': 'Пустой запрос'}, status=400)

    try:
        result = subprocess.run(
            ['C:\\Users\\20kat\\Desktop\\Fishnet_bot\\venv\\Scripts\\python.exe', 'parser.py', user_input],
            capture_output=True,
            encoding='utf-8',  # <--- вот это добавили!
            timeout=120
        )

        return Response({'stdout': result.stdout, 'stderr': result.stderr})
    except Exception as e:
        return Response({'error': str(e)}, status=500)

print("Python executable:", sys.executable)
print("PATH:", os.environ.get("PATH"))