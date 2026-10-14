// Initial Mock Data for Surplus Food
const surplusData = [
    {
        id: 1,
        foodType: "أرز بخاري ودجاج مظبي (فائض ولائم)",
        quantity: 45,
        expiryHours: 3,
        providerName: "مطاعم الرومانسية",
        location: "الباحة - العزيزية",
        urgent: true
    },
    {
        id: 2,
        foodType: "وجبات معجنات ومخبوزات مغلفة",
        quantity: 90,
        expiryHours: 5,
        providerName: "مخبز وريتاج الفاخر",
        location: "الباحة - وسط المدينة",
        urgent: false
    },
    {
        id: 3,
        foodType: "سلال فواكه وخضروات طازجة",
        quantity: 120,
        expiryHours: 10,
        providerName: "أسواق ومتاجر المزرعة",
        location: "الباحة - طريق الملك فهد",
        urgent: false
    }
];

// Render Surplus Cards
function renderSurplusCards() {
    const grid = document.getElementById("surplusGrid");
    if (!grid) return;
    grid.innerHTML = "";

    surplusData.forEach(item => {
        const card = document.createElement("div");
        card.className = `surplus-card ${item.urgent ? 'urgent' : ''}`;
        card.innerHTML = `
            <h3>${item.foodType}</h3>
            <div class="surplus-info">
                <p>📦 <strong>الكمية:</strong> ${item.quantity} وحدة</p>
                <p>⏳ <strong>الصلاحية:</strong> ${item.expiryHours} ساعات</p>
                <p>🏬 <strong>المنشأة:</strong> ${item.providerName}</p>
                <p>📍 <strong>الموقع:</strong> ${item.location}</p>
            </div>
            <button class="btn btn-primary btn-block" onclick="claimMeal(${item.id})">حجز الفائض للجمعية 🚚</button>
        `;
        grid.appendChild(card);
    });
}

// Handle Donation Form
document.getElementById("donationForm")?.addEventListener("submit", function(e) {
    e.preventDefault();

    const foodType = document.getElementById("foodType").value;
    const quantity = parseInt(document.getElementById("quantity").value);
    const expiryHours = parseInt(document.getElementById("expiryHours").value);
    const providerName = document.getElementById("providerName").value;
    const location = document.getElementById("location").value;

    const newItem = {
        id: Date.now(),
        foodType,
        quantity,
        expiryHours,
        providerName,
        location,
        urgent: expiryHours <= 3
    };

    surplusData.unshift(newItem);
    renderSurplusCards();

    // Update Stats Counter
    const statMealsEl = document.getElementById("statMeals");
    const currentMeals = parseInt(statMealsEl.textContent.replace(/,/g, ''));
    statMealsEl.textContent = (currentMeals + quantity).toLocaleString();

    this.reset();
    alert("تم تسجيل التبرع بنجاح ونشره للجمعيات القريبة! (AI Ingestion Verified)");
});

// Claim Meal Action
function claimMeal(id) {
    const index = surplusData.findIndex(item => item.id === id);
    if (index !== -1) {
        alert(`تم حجز الوجبة بنجاح وجاري إرسال إحداثيات الموقع وتوجيه المندوب السائق لاستلامها.`);
        surplusData.splice(index, 1);
        renderSurplusCards();
    }
}

// Contact Charity
function contactCharity(name) {
    alert(`جاري التواصل الفوري مع غرفة عمليات جمعية (${name})...`);
}

// Modal handling for Roles Login
function openLoginModal(role) {
    const modal = document.getElementById("loginModal");
    const modalBody = document.getElementById("modalBody");
    modal.style.display = "flex";

    if (role === 'restaurant') {
        modalBody.innerHTML = `
            <h3 style="color:var(--primary-color); margin-bottom:1rem;">تسجيل دخول المطاعم[span_9](start_span)[span_9](end_span)</h3>
            <div class="form-group"><label>اسم المستخدم أو بريد المنشأة[span_10](start_span)[span_10](end_span)</label><input type="text" placeholder="name@restaurant.com"></div>
            <div class="form-group"><label>كلمة المرور[span_11](start_span)[span_11](end_span)</label><input type="password" placeholder="••••••••"></div>
            <button class="btn btn-primary btn-block" onclick="closeLoginModal(); alert('تم تسجيل الدخول بنجاح كمنشأة غذائية')">دخول النظام</button>
        `;
    } else if (role === 'charity') {
        modalBody.innerHTML = `
            <h3 style="color:var(--primary-color); margin-bottom:1rem;">تسجيل دخول الجمعيات الخيرية[span_12](start_span)[span_12](end_span)</h3>
            <div class="form-group"><label>رقم ترخيص الجمعية (معتمد من الوزارة)[span_13](start_span)[span_13](end_span)</label><input type="text" placeholder="مثال: 1092-NGO"></div>
            <div class="form-group"><label>كلمة المرور[span_14](start_span)[span_14](end_span)</label><input type="password" placeholder="••••••••"></div>
            <button class="btn btn-primary btn-block" onclick="closeLoginModal(); alert('تم التحقق من الترخيص وتسجيل الدخول بنجاح')">تحقق ودخول</button>
        `;
    } else {
        modalBody.innerHTML = `
            <h3 style="color:var(--primary-color); margin-bottom:1rem;">تسجيل دخول الأفراد[span_15](start_span)[span_15](end_span)</h3>
            <div class="form-group"><label>رقم الجوال أو البريد الإلكتروني[span_16](start_span)[span_16](end_span)</label><input type="text" placeholder="05XXXXXXXX"></div>
            <div class="form-group"><label>كلمة المرور[span_17](start_span)[span_17](end_span)</label><input type="password" placeholder="••••••••"></div>
            <button class="btn btn-primary btn-block" onclick="closeLoginModal(); alert('مرحباً بك، تم تسجيل دخول الفرد بنجاح')">تسجيل الدخول</button>
        `;
    }
}

function closeLoginModal() {
    document.getElementById("loginModal").style.display = "none";
}

// Theme Toggle
document.getElementById("themeToggle")?.addEventListener("click", () => {
    document.body.classList.toggle("dark-theme");
    const isDark = document.body.classList.contains("dark-theme");
    document.getElementById("themeToggle").textContent = isDark ? "☀️" : "🌙";
});

// Initialize on load
document.addEventListener("DOMContentLoaded", () => {
    renderSurplusCards();
});
