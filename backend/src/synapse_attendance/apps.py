from django.apps import AppConfig

class SynapseAttendanceConfig(AppConfig):
    """
    AppConfig for the synapse_attendance app.
    
    This class allows Django projects to correctly discover and
    configure the attendance module from the Synapse-Framework.
    The 'name' attribute is crucial for the Django app registry.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'synapse_attendance'
    verbose_name = 'Synapse Attendance'
