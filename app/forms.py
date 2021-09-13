from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from wtforms.widgets.html5 import NumberInput
from wtforms_html5 import AutoAttrMeta

from app.constants import MINIMUM_CONSUMPTION, MAXIMUM_CONSUMPTION, DEFAULT_NON_MOTORWAY_CONSUMPTION, \
    DEFAULT_MOTORWAY_130KMH_CONSUMPTION, DEFAULT_MOTORWAY_110KMH_CONSUMPTION

consumption_validator = NumberRange(min=MINIMUM_CONSUMPTION,
                                    max=MAXIMUM_CONSUMPTION)


class RouteForm(FlaskForm):
    class Meta(AutoAttrMeta):
        pass

    origin = StringField('Départ', validators=[DataRequired()])
    destination = StringField('Arrivée', validators=[DataRequired()])
    non_motorway_consumption = DecimalField('Consommation hors autoroute',
                                            default=DEFAULT_NON_MOTORWAY_CONSUMPTION,
                                            widget=NumberInput(),
                                            validators=[DataRequired(),
                                                        consumption_validator])
    motorway_consumption_130 = DecimalField('Consommation à 130 km/h',
                                            default=DEFAULT_MOTORWAY_130KMH_CONSUMPTION,
                                            widget=NumberInput(),
                                            validators=[DataRequired(),
                                                        consumption_validator])
    motorway_consumption_110 = DecimalField('Consommation à 110 km/h',
                                            default=DEFAULT_MOTORWAY_110KMH_CONSUMPTION,
                                            widget=NumberInput(),
                                            validators=[DataRequired(),
                                                        consumption_validator])
    submit = SubmitField('Calculer')
