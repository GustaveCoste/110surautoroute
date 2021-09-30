from flask_wtf import FlaskForm
from wtforms import HiddenField, DecimalField, SubmitField, SelectField, FloatField
from wtforms.validators import DataRequired, NumberRange
from wtforms.widgets.html5 import NumberInput
from wtforms_html5 import AutoAttrMeta

from app.constants import MINIMUM_CONSUMPTION, MAXIMUM_CONSUMPTION, VEHICLE_TYPES, FUEL_TYPES
from app.utils import get_fuel_prices

consumption_validator = NumberRange(min=MINIMUM_CONSUMPTION,
                                    max=MAXIMUM_CONSUMPTION)


class RouteForm(FlaskForm):
    class Meta(AutoAttrMeta):
        pass

    start_lon = HiddenField('start_lon',
                            validators=[DataRequired()])
    start_lat = HiddenField('start_lat',
                            validators=[DataRequired()])
    end_lon = HiddenField('end_lon',
                          validators=[DataRequired()])
    end_lat = HiddenField('end_lat',
                          validators=[DataRequired()])
    vehicle_type = SelectField('Type de véhicule',
                               default=VEHICLE_TYPES[2],
                               choices=VEHICLE_TYPES,
                               validators=[DataRequired()])
    fuel_type = SelectField('Type de carburant',
                            default=FUEL_TYPES[0],
                            choices=FUEL_TYPES,
                            validators=[DataRequired()])
    fuel_price = DecimalField('Prix du carburant',
                              widget=NumberInput(),
                              validators=[DataRequired()])
    non_motorway_consumption = DecimalField('Consommation hors autoroute',
                                            widget=NumberInput(),
                                            validators=[DataRequired(),
                                                        consumption_validator])
    motorway_consumption_130 = DecimalField('Consommation à 130 km/h',
                                            widget=NumberInput(),
                                            validators=[DataRequired(),
                                                        consumption_validator])
    motorway_consumption_110 = DecimalField('Consommation à 110 km/h',
                                            widget=NumberInput(),
                                            validators=[DataRequired(),
                                                        consumption_validator])
    submit = SubmitField('Calculer')
