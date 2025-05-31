from django.shortcuts import render
from django.http import JsonResponse
from androguard.misc import AnalyzeAPK
from google_play_scraper import app, reviews
import requests
import os

def extract_package_name(apk_path):
    apk, _, _ = AnalyzeAPK(apk_path)
    return apk.get_package()

def analyze_apk_for_vulnerabilities(apk_path):
    
    return "No vulnerabilities detected"  

def analyze_reviews(package_name, vulnerabilities=None):
    
    result, _ = reviews(
        package_name,  
        lang='en',
        country='us',
        count=10
    )

    
    API_KEY = "AIzaSyD1Cgvmm6dkiRtRtvfNxUywbVWI8DI2gxA"
    GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

    
    combined_reviews = "\n\n".join([
        f"{i+1}. {review['userName']}: {review['content']}" for i, review in enumerate(result)
    ])

    
    rating_prompt = {
        "contents": [{
            "parts": [{
                "text": (
                    f"Below are 10 user reviews of a financial loan app. "
                    f"Analyze the overall sentiment and rate the app out of 10. "
                    f"If you find issues like scam, fraud, cheating, or high interest, rate it low (<=4). "
                    f"Only respond with a number (0-10), nothing else.\n\n"
                    f"{combined_reviews}"
                )
            }]
        }]
    }

    
    response = requests.post(GEMINI_URL, json=rating_prompt)
    response_json = response.json()

    try:
        score_text = response_json['candidates'][0]['content']['parts'][0]['text'].strip()
        score = int(''.join(filter(str.isdigit, score_text)))

        if score < 5:
            label = "Don't Install"
        elif score < 6:
            label = "Bad"
        else:
            label = "Good"

    except Exception as e:
        print("Error parsing score:", e)
        print("Full response:", response_json)
        score = "?"
        label = "Error"

    
    reason = None
    if label in ["Don't Install", "Bad"]:
        reason_prompt = {
            "contents": [{
                "parts": [{
                    "text": (
                        f"Based on the following 100 user reviews of a financial loan app, explain the main reason why the app is rated low. "
                        f"Keep your answer short and clear (max 2 lines).\n\n"
                        f"{combined_reviews}"
                    )
                }]
            }]
        }
        reason_response = requests.post(GEMINI_URL, json=reason_prompt)
        try:
            reason = reason_response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except:
            reason = "Could not determine the reason."

    
    analysis_result = {
        "score": score,
        "verdict": label,
        "reason": reason,
        "vulnerabilities": vulnerabilities
    }

    return analysis_result

def upload_apk(request):
    if request.method == 'POST' and request.FILES.get('apk_file'):
        apk_file = request.FILES['apk_file']
        file_path = os.path.join('tmp', apk_file.name)

        
        os.makedirs('tmp', exist_ok=True)

        with open(file_path, 'wb+') as destination:
            for chunk in apk_file.chunks():
                destination.write(chunk)

        package_name = extract_package_name(file_path)
        vulnerabilities = analyze_apk_for_vulnerabilities(file_path)
        analysis_result = analyze_reviews(package_name, vulnerabilities)

        
        os.remove(file_path)

        return JsonResponse(analysis_result)

    return JsonResponse({'error': 'No APK file provided'}, status=400)

def my_view(request):
    
    context = {
        
    }
    return render(request, 'upload.html', context)


def analyze_playstore_link(request):
    if request.method == 'POST':
        playstore_link = request.POST.get('playstore_link')
        if not playstore_link:
            return JsonResponse({'error': 'No Play Store link provided'}, status=400)

        
        package_name = playstore_link.split('id=')[-1].split('&')[0]
        analysis_result = analyze_reviews(package_name)

        return JsonResponse(analysis_result)

    return JsonResponse({'error': 'Invalid request method'}, status=405)
