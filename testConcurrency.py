import requests
from concurrent.futures import ThreadPoolExecutor

url = "https://cs348-437004.uc.r.appspot.com/borrow_book/{user_id}/{book_id}"

def borrow_book_request(user_id, book_id):
    try:
        response = requests.post(url.format(user_id=user_id, book_id=book_id))
        try:
            json_response = response.json()
            print(f"User {user_id} - Book {book_id}: {response.status_code} - {json_response}")
        except ValueError:
            print(f"User {user_id} - Book {book_id}: Invalid JSON response - {response.text}")
    except Exception as e:
        print(f"Error for User {user_id} - Book {book_id}: {e}")

if __name__ == "__main__":
    with ThreadPoolExecutor() as executor:
        executor.submit(borrow_book_request, 2, 5)
        executor.submit(borrow_book_request, 3, 5) 
