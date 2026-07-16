from contextlib import contextmanager

from sqlalchemy.orm import joinedload

from db.db import SessionLocal
from db.models import Recommendation


@contextmanager
def get_db():

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def getAll():

    try:

        with get_db() as db:

            recommendations = (
                db.query(Recommendation)
                .options(
                    joinedload(Recommendation.room),
                    joinedload(Recommendation.table)
                )
                .order_by(Recommendation.id.desc())
                .all()
            )

            return [
                recommendation.to_dict()
                for recommendation in recommendations
            ], None

    except Exception as e:

        return None, str(e)

def create(room_id, table_id, user_id, score, explanation, generated_image):

    try:

        with get_db() as db:

            recommendation = Recommendation(
                room_id=room_id,
                table_id=table_id,
                user_id=user_id,
                score=score,
                explanation=explanation,
                generated_image=generated_image
            )

            db.add(recommendation)

            db.commit()

            db.refresh(recommendation)

            return recommendation.to_dict(), None

    except Exception as e:

        return None, str(e)
    

def getById(id):

    try:

        with get_db() as db:

            recommendation = (
                db.query(Recommendation)
                .options(
                    joinedload(Recommendation.room),
                    joinedload(Recommendation.table)
                )
                .filter(Recommendation.id == id)
                .first()
            )

            if not recommendation:
                return None, "Recommendation not found"

            return recommendation.to_dict(), None

    except Exception as e:

        return None, str(e)


def delete(id):

    try:

        with get_db() as db:

            recommendation = (
                db.query(Recommendation)
                .filter(Recommendation.id == id)
                .first()
            )

            if not recommendation:
                return False, "Recommendation not found"

            db.delete(recommendation)

            db.commit()

            return True, None

    except Exception as e:

        return False, str(e)