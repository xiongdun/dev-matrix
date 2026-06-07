# FastAPI 最佳实践

## 依赖注入

```python
# 正确
@router.get("/items")
async def get_items(db: Session = Depends(get_db)):
    ...

# 错误
@router.get("/items")
async def get_items():
    db = SessionLocal()  # 不要手动创建
```

## 路由定义

```python
# 正确：空字符串避免 307 重定向
@router.get("")

# 错误：尾部斜杠会导致 307
@router.get("/")
```

## 错误处理

```python
# 正确
try:
    db.add(item)
    db.commit()
except Exception:
    db.rollback()
    raise
```

## 认证

```python
# 受保护端点
@router.get("/protected")
async def protected(user: UserModel = Depends(get_current_user)):
    ...
```
