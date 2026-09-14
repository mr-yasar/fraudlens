"""Initial schema for 7 core tables

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-09-13 10:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='analyst', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. customers table
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('customer_id', sa.String(length=100), nullable=False),
        sa.Column('account_age_days', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_customers_id'), 'customers', ['id'], unique=False)
    op.create_index(op.f('ix_customers_customer_id'), 'customers', ['customer_id'], unique=True)

    # 3. transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('transaction_id', sa.String(length=100), nullable=False),
        sa.Column('customer_id', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('transaction_hour', sa.Integer(), nullable=False),
        sa.Column('merchant_category', sa.String(length=100), nullable=True),
        sa.Column('transaction_country', sa.String(length=10), nullable=True),
        sa.Column('geo_location_region', sa.String(length=100), nullable=True),
        sa.Column('device_type', sa.String(length=50), nullable=True),
        sa.Column('transaction_type', sa.String(length=50), nullable=True),
        sa.Column('fraud_probability', sa.Float(), nullable=True),
        sa.Column('prediction', sa.Integer(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('risk_level', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.customer_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)
    op.create_index(op.f('ix_transactions_transaction_id'), 'transactions', ['transaction_id'], unique=True)
    op.create_index(op.f('ix_transactions_customer_id'), 'transactions', ['customer_id'], unique=False)
    op.create_index(op.f('ix_transactions_created_at'), 'transactions', ['created_at'], unique=False)
    op.create_index('ix_transactions_prediction_risk', 'transactions', ['prediction', 'risk_level'], unique=False)
    op.create_index('ix_transactions_cust_created', 'transactions', ['customer_id', 'created_at'], unique=False)

    # 4. investigations table
    op.create_table(
        'investigations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('case_id', sa.String(length=100), nullable=False),
        sa.Column('transaction_id', sa.String(length=100), nullable=False),
        sa.Column('investigator_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='open', nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['investigator_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.transaction_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_investigations_id'), 'investigations', ['id'], unique=False)
    op.create_index(op.f('ix_investigations_case_id'), 'investigations', ['case_id'], unique=True)
    op.create_index(op.f('ix_investigations_transaction_id'), 'investigations', ['transaction_id'], unique=False)
    op.create_index(op.f('ix_investigations_investigator_id'), 'investigations', ['investigator_id'], unique=False)
    op.create_index(op.f('ix_investigations_status'), 'investigations', ['status'], unique=False)
    op.create_index('ix_investigations_status_created', 'investigations', ['status', 'created_at'], unique=False)

    # 5. shap_explanations table
    op.create_table(
        'shap_explanations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('transaction_id', sa.String(length=100), nullable=False),
        sa.Column('feature_name', sa.String(length=100), nullable=False),
        sa.Column('shap_value', sa.Float(), nullable=False),
        sa.Column('impact', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.transaction_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_shap_explanations_id'), 'shap_explanations', ['id'], unique=False)
    op.create_index(op.f('ix_shap_explanations_transaction_id'), 'shap_explanations', ['transaction_id'], unique=False)
    op.create_index('ix_shap_tx_feature', 'shap_explanations', ['transaction_id', 'feature_name'], unique=False)

    # 6. model_versions table
    op.create_table(
        'model_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('precision', sa.Float(), nullable=True),
        sa.Column('recall', sa.Float(), nullable=True),
        sa.Column('f1_score', sa.Float(), nullable=True),
        sa.Column('roc_auc', sa.Float(), nullable=True),
        sa.Column('pr_auc', sa.Float(), nullable=True),
        sa.Column('model_path', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('trained_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model_name', 'version', name='uq_model_version_name_ver'),
    )
    op.create_index(op.f('ix_model_versions_id'), 'model_versions', ['id'], unique=False)
    op.create_index(op.f('ix_model_versions_model_name'), 'model_versions', ['model_name'], unique=False)

    # 7. audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_logs_created_at'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_table('audit_logs')

    op.drop_index(op.f('ix_model_versions_model_name'), table_name='model_versions')
    op.drop_index(op.f('ix_model_versions_id'), table_name='model_versions')
    op.drop_table('model_versions')

    op.drop_index('ix_shap_tx_feature', table_name='shap_explanations')
    op.drop_index(op.f('ix_shap_explanations_transaction_id'), table_name='shap_explanations')
    op.drop_index(op.f('ix_shap_explanations_id'), table_name='shap_explanations')
    op.drop_table('shap_explanations')

    op.drop_index('ix_investigations_status_created', table_name='investigations')
    op.drop_index(op.f('ix_investigations_status'), table_name='investigations')
    op.drop_index(op.f('ix_investigations_investigator_id'), table_name='investigations')
    op.drop_index(op.f('ix_investigations_transaction_id'), table_name='investigations')
    op.drop_index(op.f('ix_investigations_case_id'), table_name='investigations')
    op.drop_index(op.f('ix_investigations_id'), table_name='investigations')
    op.drop_table('investigations')

    op.drop_index('ix_transactions_cust_created', table_name='transactions')
    op.drop_index('ix_transactions_prediction_risk', table_name='transactions')
    op.drop_index(op.f('ix_transactions_created_at'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_customer_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_transaction_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_id'), table_name='transactions')
    op.drop_table('transactions')

    op.drop_index(op.f('ix_customers_customer_id'), table_name='customers')
    op.drop_index(op.f('ix_customers_id'), table_name='customers')
    op.drop_table('customers')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
