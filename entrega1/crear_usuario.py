import sys

sys.path.insert(0, "client")
import virtuallab_client

url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:80"

print("Crear un usuario nuevo")
name = input("Nombre: ").strip()
id = input("Número de identificación: ").strip()
role = ""
while role not in ("estudiante", "profesor"):
    role = input("Rol (estudiante o profesor): ").strip().lower()
password = input("Contraseña: ").strip()

print()
print("Registro:     ", virtuallab_client.registerUser(url, name, id, role, password))
print("Inicio sesión:", virtuallab_client.openSession(url, id, password))

if role == "estudiante":
    print("Mis prácticas:", virtuallab_client.listStudentLabs(url, id))
else:
    print("Estudiantes:  ", virtuallab_client.listStudents(url, id))

print("Cierre sesión:", virtuallab_client.closeSession(url, id))
print()
print("Abre server/users.txt para ver el usuario guardado.")
