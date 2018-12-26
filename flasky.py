import os
import click
from dotenv import load_dotenv
from flask.cli import FlaskGroup

# from flask_migrate import Migrate

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from app import create_app, db

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
cli = FlaskGroup(create_app=create_app)


# migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db)


@app.cli.command()
def hi():
    click.echo("Hi Hello Bye")


@app.cli.command()
def recreatedb():
    db.drop_all()
    db.create_all()
    db.session.commit()


if __name__ == '__main__':
    cli()
