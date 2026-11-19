# Se deben codificar las siguientes funciones y replicar la funcionalidad descrita en los comentarios
# Además, para la gestión de usuarios y prácticas de laboratorio se debe hacer uso de archivos de texto no se permite
# el uso de motores de bases de datos

import os
from json import dumps # Convertir diccionario a JSON
from json import loads # Convertir JSON a diccionario

usersFile = "server/users.txt"
assignmentsFile = "server/assignments.txt" # Una línea JSON por asignación o formato plano (student_id:lab)
labsDir = "server/labs"

# Identificadores de los usuarios que tienen la sesión abierta
openSessions = set()

def writeUserDataToFile(user_data):
    with open(usersFile, "a", encoding="utf-8") as file:
        file.write(dumps(user_data) + "\n")

# Retorna el diccionario del usuario con el id dado o None si no está registrado
def getUser(id):
    try:
        with open(usersFile, "r", encoding="utf-8") as file:
            for line in file:
                cleaned_line = line.strip()
                if cleaned_line == "":
                    continue
                try:
                    user = loads(cleaned_line)
                    if str(user["id"]) == str(id):
                        return user
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    return None

# Retorna True si el usuario tiene el rol indicado y se encuentra con sesión abierta
def hasRoleAndSession(id, role):
    user = getUser(id)
    return user is not None and user["role"] == role and str(id) in openSessions

# Retorna la lista de asignaciones guardadas en el archivo de texto
def readAssignments():
    assignments = []
    if not os.path.exists(assignmentsFile):
        return assignments
    try:
        with open(assignmentsFile, "r", encoding="utf-8") as file:
            for line in file:
                cleaned_line = line.strip()
                if cleaned_line == "":
                    continue
                
                # Procesa el formato plano del profesor (estudiante:laboratorio)
                if ":" in cleaned_line:
                    try:
                        parts = cleaned_line.split(":")
                        student_id = parts[0].strip()
                        lab_name = parts[1].strip()
                        
                        assignments.append({
                            "student_id": student_id,
                            "lab": lab_name
                        })
                        continue
                    except Exception:
                        pass

                # Si no tiene dos puntos, intenta cargarlo como JSON por si acaso
                try:
                    assignments.append(loads(cleaned_line))
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    return assignments

# Las prácticas son archivos zip, se acepta el nombre con o sin la extensión .zip
def labFileName(lab_name):
    if lab_name.endswith(".zip"):
        return lab_name
    return lab_name + ".zip"

# Función para registrar un usuario
def registerUser(name, id, role, password):
    if getUser(id) is not None:
        response = "User already registered"
        print(response)
        return response

    user_data = {
        "name": name,
        "id": str(id),
        "role": role,
        "password": password
    }
    writeUserDataToFile(user_data)
    response = f"User {name} with role {role} registered"
    print(response)
    return response

# Función que abre una sesión
def openSession(id, password):
    user = getUser(id)
    if user is None or user["password"] != password:
        response = "error"
        print(response)
        return response

    openSessions.add(str(id))
    response = "Session was succesfully opened"
    print(response)
    return response

# Función que cierra una sesión
def closeSession(id):
    if str(id) not in openSessions:
        response = "error"
        print(response)
        return response

    openSessions.remove(str(id))
    response = "Session was succesfully closed"
    print(response)
    return response

# Función para recibir una práctica de laboratorio (archivo zip) de un profesor
def uploadLab(id, file_name, file_data):
    if not hasRoleAndSession(id, "professor"):
        response = "error"
        print(response)
        return response

    upload_dir = labsDir
    os.makedirs(upload_dir, exist_ok=True)

    target_path = os.path.join(upload_dir, file_name)
    with open(target_path, "wb") as f:
        f.write(file_data)
    response = "File was succesfully received"
    print(response)
    return response

# Función para enviar una práctica de laboratorio (archivo zip) a un estudiante
def downloadLab(id, file_name):
    response = "error"        

    if not hasRoleAndSession(id, "student"):
        print(response)
        return response

    assigned = False
    for assignment in readAssignments():
        s_id = assignment.get("student_id")
        l_name = assignment.get("lab")
        
        if s_id is not None and l_name is not None:
            if str(s_id) == str(id) and l_name == file_name:
                assigned = True
                break
                
    if not assigned:
        print(response)
        return response

    upload_dir = labsDir
    file_path = os.path.join(upload_dir, file_name)
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            response = f"downloadLab called by user {id}"
            print(response)
            return data
    except FileNotFoundError:
        print(response)
        return response

# Función para listar las prácticas de laboratorio disponibles para un estudiante
def listStudentLabs(id):
    if not hasRoleAndSession(id, "student"):
        response = "error"
        print(response)
        return response

    labs = []
    seen = set()

    for assignment in readAssignments():
        s_id = assignment.get("student_id")
        l_name = assignment.get("lab")
        
        if s_id is not None and l_name is not None:
            if str(s_id) == str(id):
                if l_name not in seen:
                    labs.append(l_name)
                    seen.add(l_name)

    response = dumps(labs)
    print(response)
    return response

# Función para listar las prácticas de laboratorio cargadas por los profesores
def listProfessorsLabs(id):
    if not hasRoleAndSession(id, "professor"):
        response = "error"
        print(response)
        return response

    labs = []
    if os.path.isdir(labsDir):
        labs = sorted(os.listdir(labsDir))

    response = dumps(labs)
    print(response)
    return response

# Función para listar los estudiantes registrados en el sistema
def listStudents(id):
    if not hasRoleAndSession(id, "professor"):
        response = "error"
        print(response)
        return response

    students = []
    try:
        with open(usersFile, "r", encoding="utf-8") as file:
            for line in file:
                cleaned_line = line.strip()
                if cleaned_line == "":
                    continue
                try:
                    user = loads(cleaned_line)
                    if user["role"] == "student":
                        students.append({"name": user["name"], "id": user["id"]})
                except Exception:
                    continue
    except FileNotFoundError:
        pass

    response = dumps(students)
    print(response)
    return response

# Función para asignar una práctica de laboratorio a un estudiante
def assignLab(id, lab_name, student_id):
    response = "error"

    # El usuario debe ser un profesor con sesión abierta
    if not hasRoleAndSession(id, "professor"):
        print(response)
        return response

    # Verificar que el estudiante exista y tenga el rol correcto
    student = getUser(student_id)
    if student is None or student["role"] != "student":
        print(response)
        return response

    # Verificar que el laboratorio exista
    file_name = labFileName(lab_name)
    lab_path = os.path.join(labsDir, file_name)

    if not os.path.isfile(lab_path):
        print(response)
        return response

    # Evitar asignar el mismo laboratorio dos veces al mismo estudiante
    assignments = readAssignments()

    for assignment in assignments:
        s_id = assignment.get("student_id")
        l_name = assignment.get("lab")
        
        if s_id is not None and l_name is not None:
            if str(s_id) == str(student_id) and l_name == file_name:
                response = f"Lab {file_name} was succesfully assigned to student {student_id}"
                print(response)
                return response

    # Guardar usando el formato plano nativo del profesor (estudiante:laboratorio)
    os.makedirs(os.path.dirname(assignmentsFile), exist_ok=True)

    with open(assignmentsFile, "a", encoding="utf-8") as file:
        file.write(f"{student_id}:{file_name}\n")

    response = f"Lab {file_name} was succesfully assigned to student {student_id}"
    print(response)
    return response
