"""Add composite indexes and playground replay

Revision ID: c3f1a8e79b02
Revises: e7d31d65bd58
Create Date: 2026-09-16 09:08:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c3f1a8e79b02'
down_revision: Union[str, Sequence[str], None] = 'e7d31d65bd58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. generated_sdks updates
    sdk_cols = [c['name'] for c in inspector.get_columns('generated_sdks')]
    sdk_indexes = [idx['name'] for idx in inspector.get_indexes('generated_sdks')]

    with op.batch_alter_table('generated_sdks', schema=None) as batch_op:
        if 'test_code' not in sdk_cols:
            batch_op.add_column(sa.Column('test_code', sa.Text(), nullable=True))
        if 'ix_generated_sdks_api_spec_id_version' not in sdk_indexes:
            batch_op.create_index('ix_generated_sdks_api_spec_id_version', ['api_spec_id', 'version'], unique=False)

    # 2. api_specs updates
    spec_indexes = [idx['name'] for idx in inspector.get_indexes('api_specs')]
    spec_unique = [u['name'] for u in inspector.get_unique_constraints('api_specs')]

    with op.batch_alter_table('api_specs', schema=None) as batch_op:
        if 'ix_api_specs_project_id_version' not in spec_indexes:
            batch_op.create_index('ix_api_specs_project_id_version', ['project_id', 'version'], unique=False)
        if 'uq_api_specs_project_id_version' not in spec_unique:
            batch_op.create_unique_constraint('uq_api_specs_project_id_version', ['project_id', 'version'])

    # 3. playground_requests updates
    play_cols = [c['name'] for c in inspector.get_columns('playground_requests')]
    with op.batch_alter_table('playground_requests', schema=None) as batch_op:
        if 'base_url' not in play_cols:
            batch_op.add_column(sa.Column('base_url', sa.String(), nullable=True))
        if 'params' not in play_cols:
            batch_op.add_column(sa.Column('params', sa.JSON(), nullable=True))
        if 'request_headers' not in play_cols:
            batch_op.add_column(sa.Column('request_headers', sa.JSON(), nullable=True))
        if 'request_body' not in play_cols:
            batch_op.add_column(sa.Column('request_body', sa.JSON(), nullable=True))
        if 'response_headers' not in play_cols:
            batch_op.add_column(sa.Column('response_headers', sa.JSON(), nullable=True))
        if 'response_body' not in play_cols:
            batch_op.add_column(sa.Column('response_body', sa.JSON(), nullable=True))
        if 'execution_time_ms' not in play_cols:
            batch_op.add_column(sa.Column('execution_time_ms', sa.Integer(), nullable=True))
        if 'error_message' not in play_cols:
            batch_op.add_column(sa.Column('error_message', sa.Text(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 3. Revert playground_requests replay columns
    play_cols = [c['name'] for c in inspector.get_columns('playground_requests')]
    with op.batch_alter_table('playground_requests', schema=None) as batch_op:
        for col in [
            'error_message',
            'execution_time_ms',
            'response_body',
            'response_headers',
            'request_body',
            'request_headers',
            'params',
            'base_url',
        ]:
            if col in play_cols:
                batch_op.drop_column(col)

    # 2. Revert api_specs unique constraint and composite index
    spec_indexes = [idx['name'] for idx in inspector.get_indexes('api_specs')]
    spec_unique = [u['name'] for u in inspector.get_unique_constraints('api_specs')]
    with op.batch_alter_table('api_specs', schema=None) as batch_op:
        if 'uq_api_specs_project_id_version' in spec_unique:
            batch_op.drop_constraint('uq_api_specs_project_id_version', type_='unique')
        if 'ix_api_specs_project_id_version' in spec_indexes:
            batch_op.drop_index('ix_api_specs_project_id_version')

    # 1. Revert generated_sdks composite index and test_code
    sdk_indexes = [idx['name'] for idx in inspector.get_indexes('generated_sdks')]
    sdk_cols = [c['name'] for c in inspector.get_columns('generated_sdks')]
    with op.batch_alter_table('generated_sdks', schema=None) as batch_op:
        if 'ix_generated_sdks_api_spec_id_version' in sdk_indexes:
            batch_op.drop_index('ix_generated_sdks_api_spec_id_version')
        if 'test_code' in sdk_cols:
            batch_op.drop_column('test_code')
