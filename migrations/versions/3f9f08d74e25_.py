"""Create User and Picture tables

Revision ID: 3f9f08d74e25
Revises:
Create Date: 2018-04-04 22:17:35.977834

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3f9f08d74e25'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('phone_number', sa.Text(), nullable=False),
        sa.Column('tc_status', sa.Enum('NOTHING', 'SENT', 'AGREED', name='tcstatus'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone_number')
    )
    op.create_table('picture',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('create_time', sa.DateTime(), nullable=False),
        sa.Column('message_sid', sa.Text(), nullable=False),
        sa.Column('converted_url', sa.Text(), nullable=True),
        sa.Column('converted_time', sa.DateTime(), nullable=True),
        sa.Column('failed', sa.Boolean(), nullable=True),
        sa.Column('style', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('picture')
    op.drop_table('user')
    op.execute('DROP TYPE tcstatus')
