import bcrypt
from django.contrib.postgres.fields.array import ArrayField
from django.utils import timezone
from django.db import models
from django.db.models import Q, CheckConstraint
from django.core.validators import MinValueValidator

SEX_CHOICES = (
    ('MALE', 'Чоловіча'),
    ('FEMALE', 'Жіноча'),
)

BENEFIT_GROUP_CHOICES = (
    ('military', 'Військові (знижка 20%)'),
    ('elderly', 'Люди похилого віку (знижка 10%)'),
    ('disabled', 'Люди з інвалідністю (знижка 5%)'),
    ('staff_family', 'Члени родин працівників (знижка 40%)'),
)

USER_TYPE_CHOICES = (
    ('REGISTRAR', 'Реєстратор'),
    ('CLINIC_HEAD', 'Керівник'),
    ('DOCTOR', 'Лікар'),
)

PRICE_LIST_STATUS_CHOICES = (
    ('ACTIVE', 'Активний'),
    ('INACTIVE', 'Неактивний'),
)

APPOINTMENT_STATUS_CHOICES = (
    ('PLANNED', 'Запланований'),
    ('CANCELED', 'Скасований'),
    ('COMPLETED', 'Завершений'),
)


class Patient(models.Model):
    first_name = models.CharField("Ім'я", max_length=255, blank=False)
    last_name = models.CharField("Прізвище", max_length=255, blank=False)
    middle_name = models.CharField("По батькові", max_length=255, blank=True, default='')
    phone_number = models.CharField("Номер телефону", max_length=15, blank=False, unique=True)
    email = models.EmailField("Електронна пошта", max_length=255, blank=False, unique=True)
    birth_date = models.DateField("Дата народження", blank=False)
    gender = models.CharField("Стать", max_length=8, choices=SEX_CHOICES, blank=False, default='Чоловіча')
    benefit_group = models.CharField("Пільгова група", max_length=50, choices=BENEFIT_GROUP_CHOICES, blank=True)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Service(models.Model):
    service_name = models.CharField("Назва послуги", max_length=100, unique=True)
    is_service_archived = models.BooleanField("Архівовано", blank=False, default=False)

    def __str__(self):
        return self.service_name


class MedicalRecord(models.Model):
    RECORD_TYPE_CHOICES = (
        ('ANALYSIS_RESULTS', 'Результати аналізів'),
        ('NECESSARY_EXAMINATIONS', 'Направлення'),
        ('DIAGNOSIS', 'Діагноз'),
    )

    title = models.CharField("Назва запису", max_length=255, blank=False, default="-")

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    record_type = models.CharField("Тип запису", max_length=255, choices=RECORD_TYPE_CHOICES, null=False)

    pdf_links = ArrayField(
        models.CharField(max_length=255),
        blank=True,
        default=list,
        verbose_name="Посилання на PDF-файли"
    )

    services = models.ManyToManyField(Service, verbose_name="Необхідні обстеження",
                                      related_name='medical_records', blank=False)
    doctor_conclusion = models.CharField("Висновок лікаря", max_length=255, blank=True)

    created_at = models.DateTimeField("Дата створення", blank=False, default=timezone.now)

    class Meta:
        constraints = [
            # Якщо record_type = 'DIAGNOSIS', то doctor_conclusion не може бути NULL
            CheckConstraint(
                check=Q(record_type='DIAGNOSIS') & ~Q(doctor_conclusion=None) |
                      ~Q(record_type='DIAGNOSIS'),
                name='check_diagnosis_doctor_conclusion'
            ),

            # Якщо record_type = 'ANALYSIS_RESULTS', то pdf_links не може бути NULL
            CheckConstraint(
                check=Q(record_type='ANALYSIS_RESULTS') & ~Q(pdf_links=None) |
                      ~Q(record_type='ANALYSIS_RESULTS'),
                name='check_analysis_pdf_links'
            ),
        ]

    def __str__(self):
        services_names = ", ".join(service.service_name for service in self.services.all())
        return f" {self.record_type} (Пацієнт: {self.patient}) {services_names}"


class Invoice(models.Model):
    discount_percent = models.IntegerField("Знижка", blank=True, null=True)
    subtotal = models.DecimalField("Сума без знижки", max_digits=12, decimal_places=2,
                                   blank=False, default=0.01, validators=[MinValueValidator(0.01)])
    total = models.DecimalField("Сума зі знижкою", max_digits=12, decimal_places=2,
                                blank=False, default=0.01, validators=[MinValueValidator(0.01)])
    paid_date = models.DateTimeField("Дата оплати", blank=False, default=timezone.now)

    def __str__(self):
        return f"Invoice {self.pk}"


class User(models.Model):
    first_name = models.CharField("Ім'я", max_length=255, blank=False)
    last_name = models.CharField("Прізвище", max_length=255, blank=False)
    middle_name = models.CharField("По батькові", max_length=255, blank=True, default=' ')
    email = models.EmailField("Електронна пошта", max_length=255, blank=False, unique=True)
    user_type = models.CharField("Тип користувача", max_length=255, choices=USER_TYPE_CHOICES, blank=False)
    services = models.ManyToManyField(Service, verbose_name="Послуги",
                                      related_name='user_doctor', blank=True)
    password_hash = models.TextField("Хеш паролю", blank=False)
    qualification = models.CharField("Кваліфікація", max_length=255, blank=False)
    verification_code = models.IntegerField("Код верифікації", null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Якщо користувач не лікар, видаляємо всі послуги
        if self.user_type != 'DOCTOR':
            self.services.clear()

    def set_password(self, raw_password):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(raw_password.encode(), salt).decode()

    def check_password(self, raw_password):
        return bcrypt.checkpw(raw_password.encode(), self.password_hash.encode())

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class PriceList(models.Model):
    name = models.CharField("Назва прайс-листу", max_length=255, blank=False)
    status = models.CharField("Стан", max_length=15, choices=PRICE_LIST_STATUS_CHOICES,
                              default='INACTIVE', blank=False)
    is_archived = models.BooleanField("Є архівованим", blank=False, default=False)
    archive_reason = models.TextField("Причина архівування", max_length=255, blank=True)
    archivation_date = models.DateTimeField("Дата архівування", null=True, blank=True)

    def __str__(self):
        return f"Прайс-лист {self.pk} "


class PriceListEntry(models.Model):
    price_list = models.ForeignKey(PriceList, on_delete=models.CASCADE, related_name='entries')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='price_entries')
    price = models.DecimalField("Вартість", max_digits=12, decimal_places=2,
                                default=0.01, blank=False, validators=[MinValueValidator(0.01)])

    def __str__(self):
        return f"Записи прайс-листа {self.pk}"


class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments', blank=False)
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments',
                               limit_choices_to={'user_type': 'DOCTOR'}, blank=False)
    price_list_entry = models.ForeignKey(PriceListEntry, on_delete=models.CASCADE,
                                         related_name='appointments', blank=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='appointments', blank=False)

    execution_status = models.CharField("Стан виконання", max_length=15, choices=APPOINTMENT_STATUS_CHOICES,
                                        default='PLANNED', blank=False)
    appointment_date = models.DateTimeField("Дата проведення", blank=True, null=True)
    completion_date = models.DateTimeField("Дата виконання", blank=True, null=True)

    def __str__(self):
        return f"Прийом {self.pk}"
