import os
import shutil
import numpy as np
try:
    import face_recognition
    import cv2
    FACE_REC_AVAILABLE = True
except ImportError:
    FACE_REC_AVAILABLE = False

class SearchManager:
    def __init__(f, api_key=None):
        f.api_key = api_key

    def search(f, image_path: str, target_database_dir: str = None) -> list:
        """
        Extrémny vektorový engine: Prehľadáva, porovnáva pomocou matematických vektorov,
        okamžite čistí pamäť a vymazáva nezhody, aby nezaplnil úložisko v mobile/Termuxe.
        """
        results = []
        
        if not FACE_REC_AVAILABLE:
            print("[SearchManager] face_recognition nie je k dispozícii.")
            return []

        try:
            input_image = face_recognition.load_image_file(image_path)
            input_encodings = face_recognition.face_encodings(input_image)
            
            if not input_encodings:
                print("[SearchManager] Na vstupnom obrázku nebola nájdená žiadna tvár.")
                return []
            
            target_vector = input_encodings[0]
            print(f"[SearchManager] Cielový vektor úspešne pripravený (512/128-D). Spúšťam hĺbkový audit...")

            search_dirs = [d for d in [target_database_dir, "dataset", "downloads", "temp_crawl"] if d and os.path.exists(d)]
            
            scanned_count = 0
            for s_dir in search_dirs:
                for root, _, files in os.walk(s_dir):
                    for file in files:
                        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.avif')):
                            file_path = os.path.join(root, file)
                            match_found = False
                            similarity = 0.0
                            distance = 999.0
                            
                            try:
                                db_img = face_recognition.load_image_file(file_path)
                                db_encs = face_recognition.face_encodings(db_img)
                                scanned_count += 1
                                
                                for db_enc in db_encs:
                                    distance = np.linalg.norm(target_vector - db_enc)
                                    similarity = max(0.0, float((1.0 - distance) * 100.0))
                                    
                                    # Prísna hranica pre reálnu zhodu tváre
                                    if similarity >= 65.0:
                                        match_found = True
                                        break
                            except Exception:
                                match_found = False

                            # KRITICKÉ: Okamžité vymazanie súboru, ak to nie je zhoda, kvôli úspore pamäte!
                            if match_found:
                                print(f"[ZHODA NÁJDENÁ!] Súbor: {file_path} | Podobnosť: {similarity:.2f}%")
                                results.append({
                                    'engine': 'Deep Vector Neural Engine (Full Scan)',
                                    'url': f"file://{file_path}",
                                    'thumbnail_url': f"file://{file_path}",
                                    'similarity': round(similarity, 2),
                                    'metadata': f"Euklidovská vzdialenosť: {round(distance, 4)}, Reálna zhoda tváre"
                                })
                            else:
                                # Okamžitá likvidácia nezhodného súboru z disku/pamäte
                                try:
                                    if os.path.exists(file_path):
                                        os.remove(file_path)
                                except Exception:
                                    pass

            print(f"[SearchManager] Sken dokončený. Skontrolovaných a prečistených súborov: {scanned_count}, Reálnych zhôd: {len(results)}")
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
        except Exception as e:
            print(f"[SearchManager] Chyba pri hĺbkovom skenovaní: {e}")

        return results
