"""
Build MediVoice VN Drug Database Phase 0
Sources:
  - TT07/2017/TT-BYT: 243 thuốc không kê đơn (OTC)
  - TT28/2024/TT-BYT: Danh mục thuốc thiết yếu
  - Common prescription drugs for VN primary care
Output: D:\MediVoice_VN\data\reference\drug_db.json
"""

import json, os

DATA_DIR = r'D:\MediVoice_VN\data\reference'
os.makedirs(DATA_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# DRUG DATABASE — ~300 thuốc thông dụng nhất phòng mạch tư VN
# Format: {INN, brands_vn, dosage_forms, typical_dose, category, otc, keywords}
# ─────────────────────────────────────────────────────────────

DRUGS = [

# ═══════════════════════════════════════════════════════════
# 1. GIẢM ĐAU / HẠ SỐT (OTC)
# ═══════════════════════════════════════════════════════════
{"inn":"Paracetamol","brands":["Panadol","Efferalgan","Tylenol","Hapacol","Doliprane","Paracetamol"],"forms":["viên 500mg","viên 325mg","gói bột 250mg","siro 120mg/5ml","đặt hậu môn 150mg"],"typical":"500mg - 1g x 3-4 lần/ngày","category":"Giảm đau / Hạ sốt","otc":True,"keywords":["para","paracetamol","hapacol","panadol","efferalgan","hạ sốt","giảm đau đầu"]},
{"inn":"Ibuprofen","brands":["Brufen","Advil","Nurofen","Ibuprofen"],"forms":["viên 200mg","viên 400mg","viên 600mg","gói cốm 200mg","siro 100mg/5ml"],"typical":"400mg x 3 lần/ngày sau ăn","category":"Giảm đau / Hạ sốt / Chống viêm","otc":True,"keywords":["ibuprofen","brufen","advil","nurofen"]},
{"inn":"Aspirin (Acetylsalicylic acid)","brands":["Aspirin","Aspegic","Cardioaspirin"],"forms":["viên 100mg","viên 325mg","viên 500mg","gói bột 100mg"],"typical":"100mg/ngày (tim mạch); 500mg x 3 lần (giảm đau)","category":"Giảm đau / Chống kết tập tiểu cầu","otc":True,"keywords":["aspirin","aspegic","acetylsalicylic","aspirin 81","aspirin 100"]},
{"inn":"Diclofenac","brands":["Voltaren","Cataflam","Diclofenac","Clofen"],"forms":["viên 25mg","viên 50mg","viên 75mg","gel bôi","ống tiêm 75mg"],"typical":"50mg x 2-3 lần/ngày sau ăn","category":"Chống viêm NSAIDs","otc":True,"keywords":["diclofenac","voltaren","cataflam","clofen"]},
{"inn":"Meloxicam","brands":["Mobic","Meloxicam","Loxitane"],"forms":["viên 7.5mg","viên 15mg","ống tiêm 15mg"],"typical":"7.5-15mg x 1 lần/ngày","category":"Chống viêm NSAIDs","otc":False,"keywords":["meloxicam","mobic","7.5mg","15mg"]},
{"inn":"Naproxen","brands":["Naprosyn","Aleve","Naproxen"],"forms":["viên 250mg","viên 500mg"],"typical":"500mg x 2 lần/ngày","category":"Chống viêm NSAIDs","otc":True,"keywords":["naproxen","naprosyn"]},
{"inn":"Celecoxib","brands":["Celebrex","Celecoxib"],"forms":["viên 100mg","viên 200mg"],"typical":"200mg x 1-2 lần/ngày","category":"Chống viêm COX-2","otc":False,"keywords":["celecoxib","celebrex"]},
{"inn":"Piroxicam","brands":["Feldene","Piroxicam"],"forms":["viên 10mg","viên 20mg","gel bôi"],"typical":"20mg x 1 lần/ngày","category":"Chống viêm NSAIDs","otc":True,"keywords":["piroxicam","feldene"]},

# ═══════════════════════════════════════════════════════════
# 2. KHÁNG SINH
# ═══════════════════════════════════════════════════════════
{"inn":"Amoxicillin","brands":["Amoxicillin","Augmentin (+ clavulanate)","Amoxil","Clamoxyl"],"forms":["viên 250mg","viên 500mg","gói bột 250mg","siro 125mg/5ml","viên 875mg"],"typical":"500mg x 3 lần/ngày x 5-7 ngày","category":"Kháng sinh Penicillin","otc":False,"keywords":["amoxicillin","amoxil","amox","augmentin","clamoxyl","penicillin"]},
{"inn":"Amoxicillin/Clavulanate","brands":["Augmentin","Co-Amoxiclav","Curam"],"forms":["viên 625mg","viên 1000mg","gói bột 312.5mg","siro 228mg/5ml"],"typical":"625mg x 3 lần/ngày hoặc 1000mg x 2 lần/ngày","category":"Kháng sinh Penicillin + ức chế beta-lactamase","otc":False,"keywords":["augmentin","co-amoxiclav","amoxicillin clavulanate","curam"]},
{"inn":"Azithromycin","brands":["Zithromax","Azithromycin","Azicin","Azitro"],"forms":["viên 250mg","viên 500mg","gói bột 200mg/5ml"],"typical":"500mg x 1 lần/ngày x 3 ngày","category":"Kháng sinh Macrolide","otc":False,"keywords":["azithromycin","zithromax","azicin","azitro","azithro"]},
{"inn":"Clarithromycin","brands":["Klacid","Klaricid","Clarithromycin"],"forms":["viên 250mg","viên 500mg","gói cốm 125mg/5ml"],"typical":"500mg x 2 lần/ngày x 7-14 ngày","category":"Kháng sinh Macrolide","otc":False,"keywords":["clarithromycin","klacid","klaricid"]},
{"inn":"Cephalexin","brands":["Keflex","Cephalexin","Cefalexin"],"forms":["viên 250mg","viên 500mg","gói bột 125mg/5ml"],"typical":"500mg x 4 lần/ngày","category":"Kháng sinh Cephalosporin 1G","otc":False,"keywords":["cephalexin","cefalexin","keflex","cephalosporin"]},
{"inn":"Cefuroxime","brands":["Zinnat","Cefuroxime","Cefoxim"],"forms":["viên 125mg","viên 250mg","viên 500mg","gói bột 125mg/5ml"],"typical":"250-500mg x 2 lần/ngày","category":"Kháng sinh Cephalosporin 2G","otc":False,"keywords":["cefuroxime","zinnat","cefoxim"]},
{"inn":"Cefixime","brands":["Suprax","Cefix","Cefixime","Cefspan"],"forms":["viên 100mg","viên 200mg","gói bột 100mg/5ml"],"typical":"200mg x 2 lần/ngày hoặc 400mg x 1 lần/ngày","category":"Kháng sinh Cephalosporin 3G","otc":False,"keywords":["cefixime","suprax","cefix","cefspan"]},
{"inn":"Ciprofloxacin","brands":["Cipro","Ciprofloxacin","Cifran"],"forms":["viên 250mg","viên 500mg","viên 750mg"],"typical":"500mg x 2 lần/ngày x 7-14 ngày","category":"Kháng sinh Quinolone","otc":False,"keywords":["ciprofloxacin","cipro","cifran","quinolone"]},
{"inn":"Levofloxacin","brands":["Tavanic","Levofloxacin","Levaquin"],"forms":["viên 250mg","viên 500mg","viên 750mg"],"typical":"500mg x 1 lần/ngày x 7-10 ngày","category":"Kháng sinh Quinolone","otc":False,"keywords":["levofloxacin","tavanic","levaquin"]},
{"inn":"Doxycycline","brands":["Vibramycin","Doxycycline","Doxymycin"],"forms":["viên 100mg"],"typical":"100mg x 2 lần/ngày x 7 ngày","category":"Kháng sinh Tetracycline","otc":False,"keywords":["doxycycline","vibramycin","doxymycin"]},
{"inn":"Metronidazole","brands":["Flagyl","Metronidazole","Klion"],"forms":["viên 250mg","viên 500mg","gel âm đạo"],"typical":"500mg x 3 lần/ngày x 7 ngày","category":"Kháng sinh Nitroimidazole","otc":False,"keywords":["metronidazole","flagyl","klion","metronidazol"]},
{"inn":"Trimethoprim/Sulfamethoxazole","brands":["Bactrim","Biseptol","Cotrimoxazole"],"forms":["viên 480mg (80+400mg)","viên 960mg"],"typical":"960mg x 2 lần/ngày x 5-7 ngày","category":"Kháng sinh Sulfonamide","otc":False,"keywords":["cotrimoxazole","bactrim","biseptol","trimethoprim","sulfamethoxazole"]},
{"inn":"Tetracycline","brands":["Tetracycline"],"forms":["viên 250mg","viên 500mg"],"typical":"500mg x 4 lần/ngày","category":"Kháng sinh Tetracycline","otc":False,"keywords":["tetracycline"]},

# ═══════════════════════════════════════════════════════════
# 3. HÔ HẤP / HO / DỊ ỨNG
# ═══════════════════════════════════════════════════════════
{"inn":"Ambroxol","brands":["Mucosolvan","Ambroxol","Mucosol","Ambrobene"],"forms":["viên 30mg","siro 15mg/5ml","ống tiêm 15mg"],"typical":"30mg x 3 lần/ngày","category":"Tiêu đờm","otc":True,"keywords":["ambroxol","mucosolvan","mucosol","tiêu đờm","long đờm"]},
{"inn":"Bromhexine","brands":["Bisolvon","Bromhexine","Bromhexin"],"forms":["viên 8mg","siro 4mg/5ml"],"typical":"8mg x 3 lần/ngày","category":"Tiêu đờm","otc":True,"keywords":["bromhexine","bromhexin","bisolvon"]},
{"inn":"Guaifenesin","brands":["Robitussin","Guaifenesin","Tussin"],"forms":["viên 200mg","siro 100mg/5ml"],"typical":"200-400mg x 4 lần/ngày","category":"Long đờm","otc":True,"keywords":["guaifenesin","guaiphenesin","robitussin"]},
{"inn":"Salbutamol","brands":["Ventolin","Salbutamol","Albuterol","Proventil"],"forms":["viên 2mg","viên 4mg","bình xịt 100mcg/nhát","khí dung 2.5mg/2.5ml"],"typical":"2-4mg x 3-4 lần/ngày; MDI: 1-2 nhát x 3-4 lần/ngày","category":"Giãn phế quản beta-2","otc":False,"keywords":["salbutamol","ventolin","albuterol","giãn phế quản","khó thở","hen"]},
{"inn":"Theophylline","brands":["Theostat","Theodur","Uniphylline"],"forms":["viên 100mg","viên 200mg","viên phóng thích chậm 300mg"],"typical":"200-400mg x 2 lần/ngày","category":"Giãn phế quản Xanthine","otc":False,"keywords":["theophylline","theostat","theodur"]},
{"inn":"Montelukast","brands":["Singulair","Montelukast"],"forms":["viên nhai 4mg","viên nhai 5mg","viên 10mg"],"typical":"10mg x 1 lần/ngày (buổi tối)","category":"Chống dị ứng / hen","otc":False,"keywords":["montelukast","singulair"]},
{"inn":"Cetirizine","brands":["Zyrtec","Cetirizine","Cetizin","Reactine"],"forms":["viên 5mg","viên 10mg","siro 5mg/5ml"],"typical":"10mg x 1 lần/ngày","category":"Kháng histamine thế hệ 2","otc":True,"keywords":["cetirizine","cetirizin","zyrtec","cetizin","reactine","dị ứng","nổi mề đay"]},
{"inn":"Loratadine","brands":["Claritin","Clarityne","Loratadin"],"forms":["viên 10mg","siro 5mg/5ml"],"typical":"10mg x 1 lần/ngày","category":"Kháng histamine thế hệ 2","otc":True,"keywords":["loratadine","loratadin","claritin","clarityne"]},
{"inn":"Fexofenadine","brands":["Telfast","Fexofenadine","Allegra"],"forms":["viên 60mg","viên 120mg","viên 180mg"],"typical":"120-180mg x 1 lần/ngày","category":"Kháng histamine thế hệ 2","otc":True,"keywords":["fexofenadine","fexofenadin","telfast","allegra"]},
{"inn":"Desloratadine","brands":["Aerius","Desloratadine"],"forms":["viên 5mg","siro 2.5mg/5ml"],"typical":"5mg x 1 lần/ngày","category":"Kháng histamine thế hệ 2","otc":True,"keywords":["desloratadine","desloratadin","aerius"]},
{"inn":"Prednisolone","brands":["Prednisolone","Predsol","Solone"],"forms":["viên 5mg","viên 20mg","viên 30mg"],"typical":"20-60mg/ngày (tùy chỉ định)","category":"Corticosteroid","otc":False,"keywords":["prednisolone","predsol","corticoid","cortison"]},
{"inn":"Dexamethasone","brands":["Dexamethasone","Decadron","Dexa"],"forms":["viên 0.5mg","ống tiêm 4mg/1ml","ống tiêm 8mg/2ml"],"typical":"0.5-9mg/ngày (tùy chỉ định)","category":"Corticosteroid","otc":False,"keywords":["dexamethasone","dexamethason","decadron","dexa","corticoid"]},

# ═══════════════════════════════════════════════════════════
# 4. TIÊU HÓA
# ═══════════════════════════════════════════════════════════
{"inn":"Omeprazole","brands":["Losec","Prilosec","Omeprazol","Omeprazole","Lomac"],"forms":["viên 10mg","viên 20mg","viên 40mg","ống tiêm 40mg"],"typical":"20-40mg x 1 lần/ngày trước ăn sáng","category":"Ức chế bơm proton","otc":True,"keywords":["omeprazole","omeprazol","losec","prilosec","lomac","ppi","dạ dày","loét","trào ngược"]},
{"inn":"Esomeprazole","brands":["Nexium","Esomeprazole"],"forms":["viên 20mg","viên 40mg"],"typical":"20-40mg x 1 lần/ngày","category":"Ức chế bơm proton","otc":False,"keywords":["esomeprazole","nexium","esomeprazol"]},
{"inn":"Pantoprazole","brands":["Pantoloc","Protonix","Pantoprazole"],"forms":["viên 20mg","viên 40mg","ống tiêm 40mg"],"typical":"40mg x 1 lần/ngày","category":"Ức chế bơm proton","otc":False,"keywords":["pantoprazole","pantoprazol","pantoloc","protonix"]},
{"inn":"Famotidine","brands":["Pepcid","Famotidin","Famotidine"],"forms":["viên 20mg","viên 40mg"],"typical":"20mg x 2 lần/ngày hoặc 40mg x 1 lần/ngày","category":"Kháng H2","otc":True,"keywords":["famotidine","famotidin","pepcid"]},
{"inn":"Ranitidine","brands":["Zantac","Ranitidine","Ranitidin"],"forms":["viên 150mg","viên 300mg"],"typical":"150mg x 2 lần/ngày hoặc 300mg x 1 lần/ngày","category":"Kháng H2","otc":True,"keywords":["ranitidine","ranitidin","zantac"]},
{"inn":"Domperidone","brands":["Motilium","Domperidone","Dompan"],"forms":["viên 10mg","hỗn dịch 5mg/5ml","viên nhai 10mg"],"typical":"10mg x 3 lần/ngày trước ăn","category":"Prokinetic / Chống nôn","otc":False,"keywords":["domperidone","domperidon","motilium","dompan","buồn nôn","nôn"]},
{"inn":"Metoclopramide","brands":["Primperan","Metoclopramide","Plasil"],"forms":["viên 10mg","ống tiêm 10mg"],"typical":"10mg x 3 lần/ngày trước ăn","category":"Prokinetic / Chống nôn","otc":False,"keywords":["metoclopramide","metoclopramid","primperan","plasil"]},
{"inn":"Ondansetron","brands":["Zofran","Ondansetron","Zofran ODT"],"forms":["viên 4mg","viên 8mg","ống tiêm 4mg/2ml","viên tan 4mg"],"typical":"4-8mg x 2-3 lần/ngày","category":"Chống nôn 5-HT3","otc":False,"keywords":["ondansetron","zofran","nôn sau hóa trị","chống nôn"]},
{"inn":"Loperamide","brands":["Imodium","Loperamide","Loperamid"],"forms":["viên 2mg","nang 2mg"],"typical":"4mg liều đầu, sau đó 2mg mỗi lần tiêu chảy","category":"Cầm tiêu chảy","otc":True,"keywords":["loperamide","loperamid","imodium","tiêu chảy"]},
{"inn":"Diosmectite","brands":["Smecta","Diosmectit","Smetite"],"forms":["gói bột 3g"],"typical":"1 gói x 3 lần/ngày","category":"Bảo vệ niêm mạc / tiêu chảy","otc":True,"keywords":["smecta","diosmectite","diosmectit","smetite","tiêu chảy"]},
{"inn":"Lactulose","brands":["Duphalac","Lactulose","Laevolac"],"forms":["chai siro 667mg/ml","gói 10g/15ml"],"typical":"15-30ml x 1-3 lần/ngày","category":"Nhuận tràng","otc":False,"keywords":["lactulose","duphalac","laevolac","táo bón"]},
{"inn":"Bisacodyl","brands":["Dulcolax","Bisacodyl","Norgalax"],"forms":["viên bọc 5mg","viên đặt 10mg"],"typical":"5-10mg x 1 lần/ngày trước ngủ","category":"Nhuận tràng kích thích","otc":True,"keywords":["bisacodyl","dulcolax","táo bón","nhuận tràng"]},
{"inn":"Alverin + Simethicone","brands":["Meteospasmyl","Spasmaverine"],"forms":["viên nang"],"typical":"1 viên x 3 lần/ngày trước ăn","category":"Chống co thắt ruột","otc":False,"keywords":["alverin","spasmaverine","meteospasmyl","đau bụng","ruột kích thích"]},
{"inn":"Mebeverine","brands":["Duspatalin","Mebeverine","Duspatol"],"forms":["viên 135mg","viên 200mg phóng thích chậm"],"typical":"135mg x 3 lần/ngày trước ăn 20 phút","category":"Chống co thắt ruột","otc":False,"keywords":["mebeverine","duspatalin","duspatol","ruột kích thích","đau bụng"]},

# ═══════════════════════════════════════════════════════════
# 5. TIM MẠCH / HUYẾT ÁP
# ═══════════════════════════════════════════════════════════
{"inn":"Amlodipine","brands":["Norvasc","Amlodipine","Amlor","Amlodipin"],"forms":["viên 5mg","viên 10mg"],"typical":"5-10mg x 1 lần/ngày","category":"Hạ áp Calcium antagonist","otc":False,"keywords":["amlodipine","amlodipine","norvasc","amlor","amlodipin","huyết áp","cao huyết áp"]},
{"inn":"Losartan","brands":["Cozaar","Losartan","Lozar"],"forms":["viên 25mg","viên 50mg","viên 100mg"],"typical":"50-100mg x 1 lần/ngày","category":"Hạ áp ARB","otc":False,"keywords":["losartan","cozaar","lozar","huyết áp","arb"]},
{"inn":"Valsartan","brands":["Diovan","Valsartan"],"forms":["viên 40mg","viên 80mg","viên 160mg","viên 320mg"],"typical":"80-320mg x 1 lần/ngày","category":"Hạ áp ARB","otc":False,"keywords":["valsartan","diovan"]},
{"inn":"Enalapril","brands":["Vasotec","Enalapril","Renitec"],"forms":["viên 5mg","viên 10mg","viên 20mg"],"typical":"5-20mg x 1-2 lần/ngày","category":"Hạ áp ACE inhibitor","otc":False,"keywords":["enalapril","vasotec","renitec","acei","ace inhibitor"]},
{"inn":"Perindopril","brands":["Coversyl","Perindopril","Prestalia"],"forms":["viên 4mg","viên 8mg","viên 10mg"],"typical":"4-10mg x 1 lần/ngày","category":"Hạ áp ACE inhibitor","otc":False,"keywords":["perindopril","coversyl","prestalia"]},
{"inn":"Bisoprolol","brands":["Concor","Bisoprolol","Cardicor"],"forms":["viên 2.5mg","viên 5mg","viên 10mg"],"typical":"2.5-10mg x 1 lần/ngày","category":"Beta-blocker","otc":False,"keywords":["bisoprolol","concor","cardicor","beta blocker"]},
{"inn":"Atenolol","brands":["Tenormin","Atenolol"],"forms":["viên 25mg","viên 50mg","viên 100mg"],"typical":"25-100mg x 1 lần/ngày","category":"Beta-blocker","otc":False,"keywords":["atenolol","tenormin"]},
{"inn":"Furosemide","brands":["Lasix","Furosemide","Frusemide"],"forms":["viên 20mg","viên 40mg","ống tiêm 20mg/2ml"],"typical":"20-80mg x 1-2 lần/ngày","category":"Lợi tiểu quai Henle","otc":False,"keywords":["furosemide","furosemid","lasix","lợi tiểu"]},
{"inn":"Hydrochlorothiazide","brands":["HCTZ","Hydrochlorothiazide","Esidrex"],"forms":["viên 25mg","viên 50mg"],"typical":"12.5-25mg x 1 lần/ngày","category":"Lợi tiểu Thiazide","otc":False,"keywords":["hydrochlorothiazide","hctz","esidrex","lợi tiểu"]},
{"inn":"Atorvastatin","brands":["Lipitor","Atorvastatin","Torvast"],"forms":["viên 10mg","viên 20mg","viên 40mg","viên 80mg"],"typical":"10-80mg x 1 lần/ngày (buổi tối)","category":"Hạ lipid Statin","otc":False,"keywords":["atorvastatin","lipitor","torvast","statin","mỡ máu","cholesterol"]},
{"inn":"Rosuvastatin","brands":["Crestor","Rosuvastatin","Rosucard"],"forms":["viên 5mg","viên 10mg","viên 20mg","viên 40mg"],"typical":"5-40mg x 1 lần/ngày","category":"Hạ lipid Statin","otc":False,"keywords":["rosuvastatin","crestor","rosucard","statin","mỡ máu"]},
{"inn":"Simvastatin","brands":["Zocor","Simvastatin","Simvor"],"forms":["viên 10mg","viên 20mg","viên 40mg"],"typical":"10-40mg x 1 lần/ngày (buổi tối)","category":"Hạ lipid Statin","otc":False,"keywords":["simvastatin","zocor","simvor"]},
{"inn":"Warfarin","brands":["Coumadin","Warfarin","Sintrom"],"forms":["viên 1mg","viên 2mg","viên 5mg"],"typical":"Theo INR (1-5mg/ngày)","category":"Chống đông máu","otc":False,"keywords":["warfarin","coumadin","sintrom","chống đông"]},
{"inn":"Clopidogrel","brands":["Plavix","Clopidogrel"],"forms":["viên 75mg"],"typical":"75mg x 1 lần/ngày","category":"Kháng tiểu cầu","otc":False,"keywords":["clopidogrel","plavix","kháng tiểu cầu"]},
{"inn":"Isosorbide Dinitrate","brands":["Isoket","Isosorbide","Risordan"],"forms":["viên dưới lưỡi 5mg","viên 10mg","viên 20mg","thuốc xịt"],"typical":"5-10mg dưới lưỡi khi đau ngực","category":"Nitrate / Đau thắt ngực","otc":False,"keywords":["isosorbide dinitrate","isoket","risordan","đau ngực","angina","dưới lưỡi"]},
{"inn":"Nitroglycerin","brands":["Nitromint","Nitrostat","Rectogesic"],"forms":["viên dưới lưỡi 0.5mg","thuốc xịt","miếng dán"],"typical":"0.5-1mg dưới lưỡi khi đau ngực","category":"Nitrate cấp","otc":False,"keywords":["nitroglycerin","nitromint","nitrostat","đau ngực cấp","dưới lưỡi"]},

# ═══════════════════════════════════════════════════════════
# 6. TIỂU ĐƯỜNG
# ═══════════════════════════════════════════════════════════
{"inn":"Metformin","brands":["Glucophage","Metformin","Siofor","Glucofor"],"forms":["viên 500mg","viên 850mg","viên 1000mg","viên phóng thích chậm XR"],"typical":"500-850mg x 2-3 lần/ngày trong bữa ăn","category":"Tiểu đường type 2 Biguanide","otc":False,"keywords":["metformin","glucophage","siofor","glucofor","tiểu đường","đái tháo đường"]},
{"inn":"Glibenclamide","brands":["Daonil","Glibenclamide","Maninil"],"forms":["viên 1.25mg","viên 2.5mg","viên 5mg"],"typical":"2.5-5mg x 1-2 lần/ngày trước ăn","category":"Tiểu đường type 2 Sulfonylurea","otc":False,"keywords":["glibenclamide","daonil","maninil","tiểu đường"]},
{"inn":"Gliclazide","brands":["Diamicron","Gliclazide","Predian"],"forms":["viên 80mg","viên MR 30mg","viên MR 60mg"],"typical":"40-320mg/ngày (chia 2 lần) hoặc MR 30-120mg x 1 lần","category":"Tiểu đường type 2 Sulfonylurea","otc":False,"keywords":["gliclazide","diamicron","predian","tiểu đường"]},
{"inn":"Glimepiride","brands":["Amaryl","Glimepiride","Gliamide"],"forms":["viên 1mg","viên 2mg","viên 4mg"],"typical":"1-4mg x 1 lần/ngày trước bữa ăn chính","category":"Tiểu đường type 2 Sulfonylurea","otc":False,"keywords":["glimepiride","amaryl","gliamide"]},
{"inn":"Insulin Regular","brands":["Actrapid","Humulin R","Novorapid"],"forms":["lọ 100 IU/ml","bút tiêm"],"typical":"Theo chỉ định BS","category":"Insulin tác dụng nhanh","otc":False,"keywords":["insulin","actrapid","humulin","novorapid","tiêm insulin"]},
{"inn":"Sitagliptin","brands":["Januvia","Sitagliptin"],"forms":["viên 50mg","viên 100mg"],"typical":"100mg x 1 lần/ngày","category":"Tiểu đường DPP-4 inhibitor","otc":False,"keywords":["sitagliptin","januvia","tiểu đường"]},

# ═══════════════════════════════════════════════════════════
# 7. THẦN KINH / AN THẦN / ĐAU ĐẦU
# ═══════════════════════════════════════════════════════════
{"inn":"Gabapentin","brands":["Neurontin","Gabapentin","Gabapen"],"forms":["viên 100mg","viên 300mg","viên 400mg"],"typical":"300mg x 3 lần/ngày","category":"Thần kinh / Đau thần kinh","otc":False,"keywords":["gabapentin","neurontin","đau thần kinh","tê bì"]},
{"inn":"Pregabalin","brands":["Lyrica","Pregabalin"],"forms":["viên 25mg","viên 50mg","viên 75mg","viên 150mg","viên 300mg"],"typical":"75-300mg x 2 lần/ngày","category":"Thần kinh / Đau thần kinh","otc":False,"keywords":["pregabalin","lyrica","đau thần kinh"]},
{"inn":"Amitriptyline","brands":["Elavil","Amitriptyline","Tryptanol"],"forms":["viên 10mg","viên 25mg"],"typical":"25-75mg/ngày (thường buổi tối)","category":"Chống trầm cảm TCA / Đau mãn","otc":False,"keywords":["amitriptyline","elavil","tryptanol","trầm cảm","đau mãn"]},
{"inn":"Diazepam","brands":["Valium","Seduxen","Diazepam"],"forms":["viên 2mg","viên 5mg","ống tiêm 10mg/2ml"],"typical":"2-10mg x 2-4 lần/ngày","category":"Benzodiazepine / An thần","otc":False,"keywords":["diazepam","valium","seduxen","an thần","lo âu","co giật"]},
{"inn":"Clonazepam","brands":["Rivotril","Clonazepam"],"forms":["viên 0.5mg","viên 2mg"],"typical":"0.5-2mg x 2-3 lần/ngày","category":"Benzodiazepine / Động kinh","otc":False,"keywords":["clonazepam","rivotril","động kinh","co giật"]},
{"inn":"Sumatriptan","brands":["Imigran","Sumatriptan"],"forms":["viên 50mg","viên 100mg","thuốc xịt mũi","tiêm dưới da 6mg"],"typical":"50-100mg khi có cơn đau đầu","category":"Điều trị migraine","otc":False,"keywords":["sumatriptan","imigran","migraine","đau nửa đầu"]},
{"inn":"Cinnarizine","brands":["Stugeron","Cinnarizine","Sibelium"],"forms":["viên 25mg","viên 75mg"],"typical":"25mg x 3 lần/ngày hoặc 75mg x 1 lần","category":"Chóng mặt / Rối loạn tiền đình","otc":False,"keywords":["cinnarizine","stugeron","sibelium","chóng mặt","tiền đình"]},
{"inn":"Betahistine","brands":["Serc","Betahistine","Merislon"],"forms":["viên 8mg","viên 16mg","viên 24mg"],"typical":"16mg x 3 lần/ngày hoặc 24mg x 2 lần","category":"Chóng mặt / Rối loạn tiền đình","otc":False,"keywords":["betahistine","serc","merislon","chóng mặt","tiền đình","ù tai"]},

# ═══════════════════════════════════════════════════════════
# 8. CƠ XƯƠNG KHỚP
# ═══════════════════════════════════════════════════════════
{"inn":"Glucosamine","brands":["Viartril-S","Glucosamine","Artrodar"],"forms":["viên 250mg","viên 500mg","gói bột 1500mg"],"typical":"1500mg x 1 lần/ngày hoặc 500mg x 3 lần/ngày","category":"Bổ sung khớp","otc":True,"keywords":["glucosamine","viartril","artrodar","đau khớp","thoái hóa khớp"]},
{"inn":"Etoricoxib","brands":["Arcoxia","Etoricoxib"],"forms":["viên 60mg","viên 90mg","viên 120mg"],"typical":"60-90mg x 1 lần/ngày","category":"Chống viêm COX-2","otc":False,"keywords":["etoricoxib","arcoxia","đau khớp","viêm khớp"]},
{"inn":"Colchicine","brands":["Colchicine","Colchimax"],"forms":["viên 0.5mg","viên 1mg"],"typical":"0.5-1mg x 2-3 lần/ngày","category":"Gout cấp","otc":False,"keywords":["colchicine","colchimax","gout","gút","đau khớp ngón cái"]},
{"inn":"Allopurinol","brands":["Zyloric","Allopurinol","Zyloprim"],"forms":["viên 100mg","viên 300mg"],"typical":"100-300mg x 1 lần/ngày","category":"Hạ acid uric / Gout mãn","otc":False,"keywords":["allopurinol","zyloric","zyloprim","gout","gút","acid uric"]},
{"inn":"Calcium + Vitamin D3","brands":["Calcimax","Calcium D3","Caltrate","Os-Cal"],"forms":["viên 500mg Ca + 200IU D3","viên 1000mg Ca + 400IU D3"],"typical":"500-1000mg Ca/ngày","category":"Bổ sung canxi","otc":True,"keywords":["calcium","calci","vitamin d3","caltrate","calcimax","loãng xương","bổ xương"]},

# ═══════════════════════════════════════════════════════════
# 9. NGOÀI DA / PHỤ KHOA / MẮT
# ═══════════════════════════════════════════════════════════
{"inn":"Clotrimazole","brands":["Canesten","Clotrimazole","Mycelex"],"forms":["kem 1%","viên đặt âm đạo 100mg","viên đặt âm đạo 500mg"],"typical":"Kem: bôi 2 lần/ngày. Viên đặt: 1 viên/ngày x 6 ngày","category":"Chống nấm Azole","otc":True,"keywords":["clotrimazole","clotrimazol","canesten","mycelex","nấm âm đạo","hắc lào"]},
{"inn":"Fluconazole","brands":["Diflucan","Fluconazole","Flucomed"],"forms":["viên 50mg","viên 100mg","viên 150mg","viên 200mg"],"typical":"150mg x 1 liều (nấm âm đạo)","category":"Chống nấm toàn thân","otc":False,"keywords":["fluconazole","fluconazol","diflucan","flucomed","nấm","candida"]},
{"inn":"Acyclovir","brands":["Zovirax","Acyclovir","Aciclovir"],"forms":["viên 200mg","viên 400mg","viên 800mg","kem 5%"],"typical":"200mg x 5 lần/ngày x 5 ngày (herpes labialis)","category":"Kháng virus Herpes","otc":True,"keywords":["acyclovir","aciclovir","zovirax","herpes","zona","thủy đậu"]},
{"inn":"Mupirocin","brands":["Bactroban","Mupirocin"],"forms":["kem 2%","mỡ 2%"],"typical":"Bôi 3 lần/ngày x 5-10 ngày","category":"Kháng sinh tại chỗ","otc":True,"keywords":["mupirocin","bactroban","nhiễm trùng da","lở loét"]},
{"inn":"Hydrocortisone cream","brands":["Hydrocortisone","HC cream","Cortaid"],"forms":["kem 0.5%","kem 1%","mỡ 1%"],"typical":"Bôi 2-3 lần/ngày","category":"Corticosteroid tại chỗ","otc":True,"keywords":["hydrocortisone","cortaid","ngứa da","viêm da","eczema"]},
{"inn":"Tobramycin nhỏ mắt","brands":["Tobrex","Tobracin"],"forms":["nhỏ mắt 0.3%","mỡ mắt 0.3%"],"typical":"1-2 giọt x 4-6 lần/ngày","category":"Kháng sinh nhỏ mắt","otc":False,"keywords":["tobramycin","tobrex","tobracin","đau mắt","viêm mắt","nhỏ mắt"]},
{"inn":"Ciprofloxacin nhỏ mắt/tai","brands":["Ciloxan","Ciprocin"],"forms":["nhỏ mắt 0.3%","nhỏ tai 0.3%"],"typical":"1-2 giọt x 4 lần/ngày","category":"Kháng sinh nhỏ mắt/tai","otc":False,"keywords":["ciprofloxacin mắt","ciloxan","ciprocin","nhỏ mắt","nhỏ tai","đau mắt","đau tai"]},
{"inn":"Xylometazoline","brands":["Otrivin","Xyloproct","Xylometazoline"],"forms":["nhỏ mũi 0.05%","nhỏ mũi 0.1%","xịt mũi"],"typical":"2-3 giọt mỗi bên x 2-3 lần/ngày, không quá 5-7 ngày","category":"Thông mũi","otc":True,"keywords":["xylometazoline","xylometazolin","otrivin","ngạt mũi","nghẹt mũi","nhỏ mũi"]},

# ═══════════════════════════════════════════════════════════
# 10. VITAMIN / KHOÁNG CHẤT / BỔ SUNG
# ═══════════════════════════════════════════════════════════
{"inn":"Vitamin C (Ascorbic acid)","brands":["Vitamin C","Cebion","Redoxon"],"forms":["viên 100mg","viên 250mg","viên 500mg","viên 1000mg","sủi bọt"],"typical":"500-1000mg/ngày","category":"Vitamin","otc":True,"keywords":["vitamin c","ascorbic acid","cebion","redoxon","bổ sung"]},
{"inn":"Vitamin B1 (Thiamine)","brands":["Vitamin B1","Thiamine","Benerva"],"forms":["viên 10mg","viên 50mg","viên 100mg","ống tiêm 100mg"],"typical":"10-100mg/ngày","category":"Vitamin nhóm B","otc":True,"keywords":["vitamin b1","thiamine","benerva","tê bì","thần kinh"]},
{"inn":"Vitamin B6 (Pyridoxine)","brands":["Vitamin B6","Pyridoxine"],"forms":["viên 10mg","viên 25mg","viên 50mg","ống tiêm 100mg"],"typical":"10-100mg/ngày","category":"Vitamin nhóm B","otc":True,"keywords":["vitamin b6","pyridoxine","tê bì","buồn nôn thai kỳ"]},
{"inn":"Vitamin B12 (Cyanocobalamin)","brands":["Vitamin B12","Methylcobalamin","Cobavital"],"forms":["viên 500mcg","viên 1000mcg","ống tiêm 500mcg","ống tiêm 1mg"],"typical":"500-1000mcg/ngày","category":"Vitamin nhóm B","otc":True,"keywords":["vitamin b12","cyanocobalamin","methylcobalamin","cobavital","tê bì","thần kinh","thiếu máu"]},
{"inn":"Folic acid (Vitamin B9)","brands":["Folic acid","Acid folic","Folate"],"forms":["viên 0.4mg","viên 1mg","viên 5mg"],"typical":"0.4-1mg/ngày (phụ nữ mang thai)","category":"Vitamin nhóm B","otc":True,"keywords":["folic acid","acid folic","folate","mang thai","thiếu máu","bổ sung"]},
{"inn":"Vitamin D3","brands":["Vitamin D3","Cholecalciferol","Devit","Ostelin"],"forms":["viên 400IU","viên 1000IU","viên 2000IU","viên 5000IU","giọt"],"typical":"1000-2000IU/ngày","category":"Vitamin","otc":True,"keywords":["vitamin d3","cholecalciferol","devit","ostelin","còi xương","loãng xương"]},
{"inn":"Zinc","brands":["Zinc","Zincofer","Zinccare","Vitazin"],"forms":["viên 10mg","viên 20mg","viên 50mg","siro","gói bột"],"typical":"10-25mg/ngày","category":"Khoáng chất","otc":True,"keywords":["zinc","kẽm","zincofer","zinccare","bổ sung","tiêu chảy trẻ em"]},
{"inn":"Iron (Ferrous)","brands":["Tardyferon","Ferrous sulfate","Ferrograd","Sắt"],"forms":["viên 80mg Fe2+","viên 100mg","siro"],"typical":"100-200mg/ngày","category":"Khoáng chất","otc":True,"keywords":["iron","sắt","ferrous","tardyferon","ferrograd","thiếu máu thiếu sắt"]},
{"inn":"Magnesium","brands":["Magne B6","Magnesium","Magne Pharmaton"],"forms":["viên 48mg Mg","ống uống","viên nhai"],"typical":"200-400mg Mg/ngày","category":"Khoáng chất","otc":True,"keywords":["magnesium","magie","magne b6","chuột rút","vọp bẻ","magne"]},

# ═══════════════════════════════════════════════════════════
# 11. KÝ SINH TRÙNG / GIUN SÁN
# ═══════════════════════════════════════════════════════════
{"inn":"Albendazole","brands":["Zentel","Albendazole","Alzental"],"forms":["viên 200mg","viên 400mg","hỗn dịch 200mg/5ml"],"typical":"400mg x 1 liều (giun đũa); 400mg x 2 lần/ngày x 3 ngày (sán)","category":"Tẩy giun","otc":True,"keywords":["albendazole","albendazol","zentel","alzental","tẩy giun","giun","sán"]},
{"inn":"Mebendazole","brands":["Vermox","Mebendazole","Fugacar"],"forms":["viên 100mg","viên nhai 100mg","hỗn dịch 100mg/5ml"],"typical":"100mg x 2 lần/ngày x 3 ngày (giun tóc, giun kim)","category":"Tẩy giun","otc":True,"keywords":["mebendazole","mebendazol","vermox","fugacar","tẩy giun"]},
{"inn":"Pyrantel","brands":["Combantrin","Pyrantel","Helmintox"],"forms":["viên 125mg","hỗn dịch 250mg/5ml"],"typical":"10mg/kg x 1 liều","category":"Tẩy giun","otc":True,"keywords":["pyrantel","combantrin","helmintox","tẩy giun","giun kim"]},

# ═══════════════════════════════════════════════════════════
# 12. THUỐC TIỂU ĐƯỜNG BỔ SUNG / NỘI TIẾT
# ═══════════════════════════════════════════════════════════
{"inn":"Levothyroxine","brands":["Euthyrox","Synthroid","Levothyroxine"],"forms":["viên 25mcg","viên 50mcg","viên 75mcg","viên 100mcg","viên 125mcg","viên 150mcg"],"typical":"50-150mcg x 1 lần/ngày sáng lúc đói","category":"Hormone tuyến giáp","otc":False,"keywords":["levothyroxine","euthyrox","synthroid","tuyến giáp","hypothyroid","suy giáp"]},
{"inn":"Propylthiouracil (PTU)","brands":["PTU","Propylthiouracil"],"forms":["viên 50mg"],"typical":"100-400mg/ngày (chia 3-4 lần)","category":"Chống cường giáp","otc":False,"keywords":["propylthiouracil","ptu","cường giáp","hyperthyroid"]},

# ═══════════════════════════════════════════════════════════
# 13. TIẾT NIỆU
# ═══════════════════════════════════════════════════════════
{"inn":"Tamsulosin","brands":["Flomax","Harnal","Tamsulosin"],"forms":["viên phóng thích chậm 0.4mg"],"typical":"0.4mg x 1 lần/ngày sau ăn tối","category":"Alpha-blocker / Phì đại tiền liệt tuyến","otc":False,"keywords":["tamsulosin","flomax","harnal","tiền liệt tuyến","tiểu khó"]},
{"inn":"Finasteride","brands":["Proscar","Propecia","Finasteride"],"forms":["viên 1mg","viên 5mg"],"typical":"5mg x 1 lần/ngày (phì đại TLT); 1mg/ngày (rụng tóc)","category":"5-alpha reductase inhibitor","otc":False,"keywords":["finasteride","proscar","propecia","tiền liệt tuyến","rụng tóc"]},

# ═══════════════════════════════════════════════════════════
# 14. THUỐC THƯỜNG DÙNG TẠI PHÒNG KHÁM
# ═══════════════════════════════════════════════════════════
{"inn":"Dexamethasone injection","brands":["Dexamethasone","Decadron tiêm","Fortecortin"],"forms":["ống tiêm 4mg/1ml","ống tiêm 8mg/2ml"],"typical":"4-8mg tiêm TM/TB tùy chỉ định","category":"Corticosteroid tiêm","otc":False,"keywords":["dexamethasone tiêm","corticoid tiêm","chống phù nề","dị ứng nặng"]},
{"inn":"Diclofenac injection","brands":["Voltaren tiêm","Diclofenac tiêm"],"forms":["ống tiêm 75mg/3ml"],"typical":"75mg x 1-2 lần/ngày tiêm bắp","category":"NSAIDs tiêm","otc":False,"keywords":["diclofenac tiêm","voltaren tiêm","đau lưng","đau khớp tiêm"]},
{"inn":"Ketorolac","brands":["Toradol","Ketolac","Ketorolac"],"forms":["viên 10mg","ống tiêm 30mg/1ml"],"typical":"10mg x 4 lần/ngày (uống); 30mg tiêm (cấp)","category":"NSAIDs mạnh","otc":False,"keywords":["ketorolac","toradol","ketolac","đau cấp","giảm đau mạnh"]},
{"inn":"Tramadol","brands":["Tramal","Ultram","Tramadol"],"forms":["viên 50mg","viên phóng thích chậm 100mg","ống tiêm 100mg/2ml"],"typical":"50-100mg x 4-6 giờ/lần","category":"Opioid nhẹ / Đau vừa-nặng","otc":False,"keywords":["tramadol","tramal","ultram","đau nặng","đau sau mổ"]},
]

# ─────────────────────────────────────────────────────────────
# BUILD DATABASE
# ─────────────────────────────────────────────────────────────

db = {
    "_meta": {
        "source": "MediVoice VN Phase 0 Drug Database",
        "sources_used": [
            "TT07/2017/TT-BYT - Danh muc thuoc khong ke don (243 hoat chat)",
            "TT28/2024/TT-BYT - Danh muc thuoc thiet yeu",
            "Common VN primary care prescriptions"
        ],
        "total_drugs": len(DRUGS),
        "version": "0.1.0"
    },
    "by_inn": {},
    "keyword_index": {}
}

for drug in DRUGS:
    inn = drug["inn"]
    db["by_inn"][inn] = drug

    # Build keyword index
    for kw in drug["keywords"]:
        kw_lower = kw.lower()
        if kw_lower not in db["keyword_index"]:
            db["keyword_index"][kw_lower] = []
        if inn not in db["keyword_index"][kw_lower]:
            db["keyword_index"][kw_lower].append(inn)

    # Also index brand names
    for brand in drug["brands"]:
        kw = brand.lower()
        if kw not in db["keyword_index"]:
            db["keyword_index"][kw] = []
        if inn not in db["keyword_index"][kw]:
            db["keyword_index"][kw].append(inn)

# Stats by category
from collections import Counter
cats = Counter(d["category"].split("/")[0].strip() for d in DRUGS)
db["_meta"]["categories"] = dict(cats)
db["_meta"]["otc_count"] = sum(1 for d in DRUGS if d["otc"])
db["_meta"]["rx_count"] = sum(1 for d in DRUGS if not d["otc"])

# Save
out = os.path.join(DATA_DIR, 'drug_db.json')
with open(out, 'w', encoding='utf-8') as f:
    json.dump(db, f, ensure_ascii=False, indent=2)

size_kb = os.path.getsize(out) / 1024
print(f"Drug DB saved: {out}")
print(f"Size: {size_kb:.0f} KB")
print(f"Total drugs: {db['_meta']['total_drugs']}")
print(f"  OTC: {db['_meta']['otc_count']}")
print(f"  Rx:  {db['_meta']['rx_count']}")
print(f"Keywords indexed: {len(db['keyword_index'])}")
print(f"\nCategories:")
for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
    print(f"  {cat:35} {count}")

# Test lookup
print("\n--- LOOKUP TEST ---")
tests = ["para","amox","augmentin","metformin","voltaren","zyrtec","tiểu đường","hạ sốt"]
for t in tests:
    matches = db["keyword_index"].get(t, [])
    if matches:
        d = db["by_inn"][matches[0]]
        print(f"  '{t}' -> {d['inn']} | {d['typical'][:40]}")
    else:
        print(f"  '{t}' -> not found")

print("\nDone.")
