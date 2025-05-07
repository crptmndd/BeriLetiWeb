from alembic import op
import sqlalchemy as sa

revision = 'd217ef56f067'
down_revision = '44f38723b2b7'
branch_labels = None
depends_on = None

def upgrade():
    # 1) Добавляем колонку со значением по умолчанию для новых и старых строк
    op.add_column(
        'orders',
        sa.Column('status', sa.String(), nullable=True, server_default='pending')
    )
    op.create_index('ix_orders_status', 'orders', ['status'], unique=False)

    # 2) Явно обновляем существующие записи (на всякий случай)
    op.execute("UPDATE orders SET status = 'pending' WHERE status IS NULL")

    # 3) Переводим колонку в NOT NULL и убираем default
    op.alter_column('orders', 'status',
        existing_type=sa.String(),
        nullable=False,
        server_default=None
    )

def downgrade():
    op.drop_index('ix_orders_status', table_name='orders')
    op.drop_column('orders', 'status')
