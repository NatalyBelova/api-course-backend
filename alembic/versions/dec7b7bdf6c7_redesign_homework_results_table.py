"""redesign homework_results table

Revision ID: dec7b7bdf6c7
Revises: 50e8d0a0b112
Create Date: 2026-08-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dec7b7bdf6c7'
down_revision: Union[str, None] = '50e8d0a0b112'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f('ix_homework_results_id'), table_name='homework_results')
    op.drop_table('homework_results')

    op.create_table(
        'homework_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('practice', sa.String(length=30), nullable=False),
        sa.Column('submitted_checks', sa.JSON(), nullable=False),
        sa.Column('submitted_notes', sa.Text(), nullable=True),
        sa.Column('fingerprint_hash', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('criteria_verdicts', sa.JSON(), nullable=False),
        sa.Column('auto_accepted', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_homework_results_id'), 'homework_results', ['id'], unique=False)
    op.create_index(
        'ix_homework_results_user_practice_fingerprint',
        'homework_results',
        ['user_id', 'practice', 'fingerprint_hash'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_homework_results_user_practice_fingerprint', table_name='homework_results')
    op.drop_index(op.f('ix_homework_results_id'), table_name='homework_results')
    op.drop_table('homework_results')

    op.create_table(
        'homework_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.String(length=100), nullable=False),
        sa.Column('task_id', sa.String(length=100), nullable=False),
        sa.Column('student_request', sa.Text(), nullable=True),
        sa.Column('student_response', sa.Text(), nullable=True),
        sa.Column('ai_result', sa.Text(), nullable=True),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_homework_results_id'), 'homework_results', ['id'], unique=False)
