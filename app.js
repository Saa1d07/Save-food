// Initial Mock Data for Surplus Food
const surplusData = [
    {
        id: 1,
        foodType: "أرز بخاري ودجاج مظبي (فائض حفل)",
        quantity: 40,
        expiryHours: 3,
        providerName: "مطاعم الرومانسية",
        location: "الرياض - حي العقيق",
        urgent: true
    },
    {
        id: 2,
        foodType: "وجبات معجنات وسندويشات مغلفة",
        quantity: 80,
        expiryHours: 6,
        providerName: "مخبز وفندق الشيراتون",
        location: "جدة - حي الشاطئ",
        urgent: false
    },
    {
        id: 3,
        foodType: "فواكه وخضروات طازجة فائضة",
        quantity: 120,
        expiryHours: 12,
        providerName: "أسواق المزرعة",
        location: "الباحة - وسط المدينة",
        urgent: false
    }
];

// Load Cards into DOM
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
                <p>📦 <strong>الكمية:</strong> ${item.quantity} وجبة</p>
                <p>⏳ <strong>الصلاحية المتبقية:</strong> ${item.expiryHours} ساعات</p>
                <p>🏬 <strong>المورد:</strong> ${item.providerName}</p>
                <p>📍 <strong>الموقع:</strong> ${item.location}</p>
            </div>
            <button class="btn btn-primary btn-block" onclick="claimMeal(${item.id})">حجز الوجبات للجمعية 🚚</button>
        `;
        grid.appendChild(card);
    });
}

// Handle New Donation Form Submission
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

    // Update Live Stats
    const statMealsEl = document.getElementById("statMeals");
    const currentMeals = parseInt(statMealsEl.textContent.replace(/,/g, ''));
    statMealsEl.textContent = (currentMeals + quantity).toLocaleString();

    // Reset Form
    this.reset();
    alert("تم نشر التبرع بنجاح! سيتم إشعار الجمعيات القريبة في منطقتك فوراً.");
});

// Claim Meal Action
function claimMeal(id) {
    const index = surplusData.findIndex(item => item.id === id);
    if (index !== -1) {
        alert(`تم طلب حجز وجبة "${surplusData[index].foodType}". تم إرسال تفاصيل الموقع إلى سائق الجمعية!`);
        surplusData.splice(index, 1);
        renderSurplusCards();
    }
}

// Contact Charity Action
function contactCharity(name) {
    alert(`جاري التوصيل بمندوب جمعية (${name})... يمكنك التنسيق المباشر الآن.`);
}

// Dark/Light Theme Toggle
document.getElementById("themeToggle")?.addEventListener("click", () => {
    document.body.classList.toggle("dark-theme");
    const isDark = document.body.classList.contains("dark-theme");
    document.getElementById("themeToggle").textContent = isDark ? "☀️" : "🌙";
});

// Initialize on Load
document.addEventListener("DOMContentLoaded", () => {
    renderSurplusCards();
});
