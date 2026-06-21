# ScholarAI Backend

A production-ready FastAPI backend for student assessment management with clear learning-focused documentation.

## 🎯 What You'll Learn

This project teaches you:
- **Framework Setup**: Industry-standard FastAPI structure
- **API Development**: Building RESTful endpoints with validation
- **Database Orchestration**: SQLAlchemy ORM and database management
- **Deterministic Rules**: Business logic separated from API
- **Pipeline Integration**: Complex workflow coordination

## 🚀 Quick Start

```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Setup environment
cp .env.example .env

# 3. Run server
python run.py
```

Visit: **http://localhost:8000/docs** to try the API

## 📚 Documentation

- **[LEARNING_GUIDE.md](./docs/LEARNING_GUIDE.md)** - Complete learning guide with explanations
- **[QUICK_REFERENCE.md](./docs/QUICK_REFERENCE.md)** - Fast workflows and code patterns

## 🏗️ Architecture

```
HTTP Request → Validation → Business Logic → Database → Response
   (Route)      (Schema)      (Rules)        (Model)
```

### Project Structure

```
app/
├── api/              # HTTP endpoints (what frontend calls)
├── core/             # Configuration & logging
├── db/               # Database & ORM models
├── rules/            # Business logic (independent of API)
└── pipeline/         # Complex multi-step workflows
```

## 🎓 Key Concepts Explained

### 1. **Models** (Database Layer)
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    name = Column(String)
```
Maps Python classes to database tables.

### 2. **Schemas** (API Validation)
```python
class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1)
```
Validates incoming requests automatically.

### 3. **Routes** (HTTP Endpoints)
```python
@router.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    return db_user
```
Handles HTTP requests.

### 4. **Rules** (Business Logic)
```python
class GradingRules:
    @staticmethod
    def calculate_grade(score: float, total: float) -> str:
        percentage = (score / total) * 100
        return "A" if percentage >= 90 else "B"
```
Reusable business logic.

### 5. **Pipelines** (Workflows)
```python
class AssessmentPipeline:
    @staticmethod
    def submit_assessment(user_id, assessment_id, score):
        # Step 1: Validate
        # Step 2: Calculate
        # Step 3: Save
        # Step 4: Return result
```
Orchestrates multi-step operations.

## 📝 API Endpoints

### Users
- `GET /users` - List all users
- `POST /users` - Create user
- `GET /users/{user_id}` - Get user with assessments
- `PUT /users/{user_id}` - Update user
- `DELETE /users/{user_id}` - Delete user

### Assessments
- `GET /users/{user_id}/assessments` - List user's assessments
- `POST /users/{user_id}/assessments` - Create assessment
- `GET /users/{user_id}/assessments/{assessment_id}` - Get assessment

### Health
- `GET /` - API status
- `GET /health` - Health check

## 💡 Common Tasks

### Add a New Endpoint
1. Add schema to `app/api/schemas.py`
2. Add database model to `app/db/models.py`
3. Create routes in `app/api/routes_*.py`
4. Register router in `app/main.py`

### Add Business Logic
1. Create rule class in `app/rules/`
2. Use rule in endpoints with `RuleClass.method(...)`

### Create Complex Workflow
1. Add pipeline class to `app/pipeline/orchestrator.py`
2. Call pipeline from endpoint

See [QUICK_REFERENCE.md](./docs/QUICK_REFERENCE.md) for detailed examples.

## 🧪 Testing

### Using Swagger UI (Easiest)
1. Visit http://localhost:8000/docs
2. Click endpoint → "Try it out"
3. Fill parameters → Execute

### Using curl
```bash
curl http://localhost:8000/users/1
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test"}'
```

## 🗄️ Database

### SQLite (Development)
```
DATABASE_URL=sqlite:///./test.db
```

### PostgreSQL (Production)
```
DATABASE_URL=postgresql://user:password@localhost/db
```

Database tables auto-create on startup. No migration needed.

## 📊 Example Workflow

```
POST /users/1/assessments
├─ Validate: Check data format
├─ Rule: Check user eligibility
├─ Save: Store in database
├─ Grading: Calculate score
└─ Response: Return result
```

## 🔧 Configuration

Edit `.env`:
```
DATABASE_URL=postgresql://...
SERVER_PORT=8000
DEBUG=True
APP_NAME=ScholarAI Backend
```

## 🎓 Learning Resources

### In This Project
- **Code Comments**: Every file has detailed explanations
- **Type Hints**: Learn typing with `str`, `int`, `List[User]`
- **Docstrings**: Every function is documented

### External
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Pydantic Validation](https://docs.pydantic.dev/)

## 📋 Workflow Files

| Need | File |
|------|------|
| New API endpoint | `app/api/routes_*.py` |
| New database table | `app/db/models.py` |
| Request validation | `app/api/schemas.py` |
| Business logic | `app/rules/` |
| Complex operation | `app/pipeline/orchestrator.py` |

## ⚠️ Important Notes

### Best Practices Used
✅ Separation of concerns (API, DB, Rules, Pipeline)
✅ Type hints for clarity and IDE support
✅ Validation at API boundary (Pydantic)
✅ Reusable business logic (Rules)
✅ Dependency injection (Depends)
✅ Comprehensive logging
✅ Error handling with proper HTTP status codes

### Before Deployment
- [ ] Set `DEBUG=False` in `.env`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure proper CORS origins
- [ ] Add authentication (JWT)
- [ ] Set up SSL/HTTPS
- [ ] Configure database backups

## 🐛 Troubleshooting

**Port already in use?**
```bash
lsof -ti:8000 | xargs kill -9
```

**Import errors?**
```bash
pip install -r requirements.txt
```

**Database errors?**
Restart server - tables auto-create.

See [LEARNING_GUIDE.md](./docs/LEARNING_GUIDE.md#troubleshooting) for more help.

## 📖 Next Steps

1. Read [LEARNING_GUIDE.md](./docs/LEARNING_GUIDE.md) for deep understanding
2. Try [QUICK_REFERENCE.md](./docs/QUICK_REFERENCE.md) workflows
3. Add your first endpoint following the patterns
4. Explore the code - every file is commented

## 📞 Questions?

Refer to documentation files for detailed explanations:
- **Setup issues?** → [LEARNING_GUIDE.md](./docs/LEARNING_GUIDE.md#troubleshooting)
- **How to add something?** → [QUICK_REFERENCE.md](./docs/QUICK_REFERENCE.md)
- **Understand a concept?** → [LEARNING_GUIDE.md](./docs/LEARNING_GUIDE.md#key-concepts)

---

**Start building! You have everything you need to succeed! 🚀**
