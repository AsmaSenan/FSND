"""empty message

Revision ID: 0ec69e1428c1
Revises: 049a12060a8e
Create Date: 2020-08-08 20:24:11.986997

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0ec69e1428c1'
down_revision = '049a12060a8e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Show',
    sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('start_time')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Show')
    # ### end Alembic commands ###
