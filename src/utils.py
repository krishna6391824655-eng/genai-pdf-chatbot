import os
def save_uploaded_file(uploaded_file):
    if not os.path.exists("temp"):
        os.makedirs("temp")

    file_path =os.path.join("temp" , uploaded_file.name)
     
    with open(file_path , "wb") as f:
        f.write(uploaded_file.getbuffer()) 
        return file_path