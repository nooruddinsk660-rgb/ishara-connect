import asyncio
import edge_tts
import os

AUDIO_DIR = "static/audio"
RATE = "-15%"  # Slightly slower for clarity
PITCH = "+0Hz"

# --- VOICES ---
VOICE_BENGALI = "bn-IN-TanishaaNeural"
VOICE_HINDI = "hi-IN-SwaraNeural"
VOICE_ENGLISH = "en-IN-NeerjaNeural"

# --- MAPS ---
BENGALI_MAP = {
    "Nothing": "", "Hello": "নমস্কার", "Thank You": "ধন্যবাদ", "Good": "খুব ভালো", "Bad": "খারাপ", "Yes": "হ্যাঁ", 
    "Water": "আমার জল লাগবে", "Food": "আমার খাবার লাগবে", "Toilet": "আমি টয়লেটে যাবো", "Medicine": "আমার ওষুধ লাগবে", 
    "Money": "আমার টাকা লাগবে", "Help": "সাহায্য করুন", "Pain": "আমার ব্যথা করছে", "Call Doctor": "ডাক্তার ডাকুন", 
    "Police": "পুলিশ ডাকুন", "Home": "আমি বাড়ি যাবো", "What": "কী?", "Where": "কোথায়?", "Time": "কটা বাজে?", 
    "I Love You": "আমি তোমাকে ভালোবাসি", "Stop": "থামুন", "No": "না", "Please": "দয়া করে", "Sorry": "ক্ষমা করুন", 
    "Friend": "বন্ধু", "Mother": "মা", "Book": "বই", "Tea": "আমি চা খাবো", "Name": "আমার নাম", "Happy": "আমি খুব খুশি"
}

HINDI_MAP = {
    "Nothing": "", "Hello": "नमस्ते", "Thank You": "धन्यवाद", "Good": "बहुत अच्छा", "Bad": "खराब", "Yes": "हाँ", 
    "Water": "मुझे पानी चाहिए", "Food": "मुझे खाना चाहिए", "Toilet": "मुझे वॉशरूम जाना है", "Medicine": "मुझे दवाई चाहिए", 
    "Money": "मुझे पैसे चाहिए", "Help": "मेरी मदद करें", "Pain": "मुझे दर्द हो रहा है", "Call Doctor": "डॉक्टर को बुलाओ", 
    "Police": "पुलिस को बुलाओ", "Home": "मुझे घर जाना है", "What": "क्या?", "Where": "कहाँ?", "Time": "समय क्या हुआ है?", 
    "I Love You": "मैं तुमसे प्यार करता हूँ", "Stop": "रुकिए", "No": "नहीं", "Please": "कृपया", "Sorry": "माफ़ करें", 
    "Friend": "दोस्त", "Mother": "माँ", "Book": "किताब", "Tea": "मुझे चाय चाहिए", "Name": "मेरा नाम", "Happy": "मैं बहुत खुश हूँ"
}

ENGLISH_MAP = {
    "Nothing": "", "Hello": "Hello", "Thank You": "Thank you", "Good": "Good", "Bad": "Bad", "Yes": "Yes", 
    "Water": "I need water", "Food": "I need food", "Toilet": "I need the washroom", "Medicine": "I need medicine", 
    "Money": "I need money", "Help": "Help me", "Pain": "I am in pain", "Call Doctor": "Call a doctor", 
    "Police": "Call the police", "Home": "I want to go home", "What": "What?", "Where": "Where?", "Time": "What time is it?", 
    "I Love You": "I love you", "Stop": "Stop", "No": "No", "Please": "Please", "Sorry": "Sorry", "Friend": "Friend", 
    "Mother": "Mother", "Book": "Book", "Tea": "I want tea", "Name": "My name is", "Happy": "I am happy"
}

# --- POLITE / FORMAL MAPS ---
BENGALI_POLITE_MAP = {
    "Nothing": "", "Hello": "আপনাকে নমস্কার", "Thank You": "আপনাকে অনেক ধন্যবাদ", "Good": "এটি খুব ভালো", "Bad": "এটি ঠিক নয়", "Yes": "আজ্ঞে হ্যাঁ", 
    "Water": "দয়া করে আমাকে একটু জল দেবেন?", "Food": "দয়া করে আমাকে একটু খাবার দেবেন?", "Toilet": "শৌচালয়টি কোনদিকে বলতে পারবেন?", 
    "Medicine": "আমার একটু ওষুধের প্রয়োজন ছিল", "Money": "আমার কিছু টাকার প্রয়োজন ছিল", "Help": "ক্ষমা করবেন, আমাকে একটু সাহায্য করতে পারবেন?", 
    "Pain": "আমার শরীরে খুব ব্যথা করছে", "Call Doctor": "দয়া করে একজন ডাক্তার ডেকে দিন", "Police": "অনুগ্রহ করে পুলিশকে খবর দিন", 
    "Home": "আমি বাড়ি ফিরে যেতে চাই", "What": "এটি কী বলতে পারবেন?", "Where": "এটি কোথায় বলতে পারবেন?", "Time": "দয়া করে কটা বাজে বলবেন?", 
    "I Love You": "আমি আপনাকে শ্রদ্ধা করি", "Stop": "দয়া করে এবার থামুন", "No": "আজ্ঞে না", "Please": "অনুগ্রহ করে", "Sorry": "দয়া করে আমাকে ক্ষমা করবেন", 
    "Friend": "আপনি আমার বন্ধু", "Mother": "মা", "Book": "আমি বইটি পড়তে চাই", "Tea": "দয়া করে আমাকে এক কাপ চা দেবেন?", "Name": "আমার নাম হলো", "Happy": "আমি আজ অত্যন্ত আনন্দিত"
}

HINDI_POLITE_MAP = {
    "Nothing": "", "Hello": "आपको नमस्कार", "Thank You": "आपका बहुत बहुत धन्यवाद", "Good": "यह बहुत अच्छा है", "Bad": "यह ठीक नहीं है", "Yes": "जी हाँ", 
    "Water": "क्या मुझे कृपया थोड़ा पानी मिल सकता है?", "Food": "क्या मुझे कृपया थोड़ा खाना मिल सकता है?", "Toilet": "क्षमा करें, वॉशरूम किस तरफ है?", 
    "Medicine": "मुझे कुछ दवाइयों की आवश्यकता है", "Money": "मुझे कुछ पैसों की आवश्यकता है", "Help": "माफ़ कीजिए, क्या आप मेरी मदद कर सकते हैं?", 
    "Pain": "मुझे बहुत दर्द महसूस हो रहा है", "Call Doctor": "कृपया एक डॉक्टर को बुला दीजिए", "Police": "कृपया पुलिस को सूचित करें", 
    "Home": "मैं अपने घर लौटना चाहता हूँ", "What": "क्या आप बता सकते हैं यह क्या है?", "Where": "क्या आप बता सकते हैं यह कहाँ है?", "Time": "कृपया बताएँगे कि समय क्या हुआ है?", 
    "I Love You": "मैं आपका आदर करता हूँ", "Stop": "कृपया अब रुक जाइए", "No": "जी नहीं", "Please": "कृपया", "Sorry": "कृपया मुझे माफ़ कर दीजिए", 
    "Friend": "आप मेरे मित्र हैं", "Mother": "माता जी", "Book": "मैं यह किताब पढ़ना चाहता हूँ", "Tea": "क्या मुझे एक कप चाय मिल सकती है?", "Name": "मेरा शुभ नाम है", "Happy": "मैं आज बहुत प्रसन्न हूँ"
}

ENGLISH_POLITE_MAP = {
    "Nothing": "", "Hello": "Greetings to you", "Thank You": "Thank you so much", "Good": "This is very good", "Bad": "I don't think this is right", "Yes": "Yes, please", 
    "Water": "Excuse me, could I please have some water?", "Food": "Could I please get something to eat?", "Toilet": "Could you please tell me where the washroom is?", 
    "Medicine": "I am in need of some medicine, please", "Money": "I require some financial assistance, please", "Help": "Excuse me, would you be able to help me?", 
    "Pain": "I am experiencing severe pain", "Call Doctor": "Could you please call a doctor for me?", "Police": "Please inform the police immediately", 
    "Home": "I would like to return home now", "What": "Could you please explain what this is?", "Where": "Could you please tell me where this is?", "Time": "Excuse me, could you tell me the time?", 
    "I Love You": "I have great respect for you", "Stop": "Could you please stop now?", "No": "No, thank you", "Please": "If you please", "Sorry": "I sincerely apologize", 
    "Friend": "You are a good friend", "Mother": "Mother", "Book": "I would like to read this book", "Tea": "Could I please have a cup of tea?", "Name": "My name is", "Happy": "I am delighted"
}

async def generate_for_map(map_data, voice, folder_name):
    # Ensure folder exists
    target_dir = os.path.join(AUDIO_DIR, folder_name)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    print(f"\n--- Processing: {folder_name} ({voice}) ---")
    
    for gesture, text in map_data.items():
        if not text: continue
        
        # Consistent Filename: "Please" -> "please.mp3"
        filename = f"{gesture.lower().replace(' ', '_')}.mp3"
        filepath = os.path.join(target_dir, filename)
        
        # print(f"Generating: {gesture} -> {filepath}")
        
        try:
            communicate = edge_tts.Communicate(text, voice, rate=RATE, pitch=PITCH)
            await communicate.save(filepath)
            print(f"✅ Generated: {filename}")
        except Exception as e:
            print(f"❌ Error generating {gesture}: {e}")

async def main():
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)
        
    # batch 1: Bengali
    await generate_for_map(BENGALI_MAP, VOICE_BENGALI, "bengali")
    await generate_for_map(BENGALI_POLITE_MAP, VOICE_BENGALI, "bengali_polite")
    
    # batch 2: Hindi
    await generate_for_map(HINDI_MAP, VOICE_HINDI, "hindi")
    await generate_for_map(HINDI_POLITE_MAP, VOICE_HINDI, "hindi_polite")
    
    # batch 3: English
    await generate_for_map(ENGLISH_MAP, VOICE_ENGLISH, "english")
    await generate_for_map(ENGLISH_POLITE_MAP, VOICE_ENGLISH, "english_polite")
    
    print("\n🎉 All Audio Assets Generated Successfully!")

if __name__ == "__main__":
    asyncio.run(main())
