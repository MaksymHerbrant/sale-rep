/**
 * C++ модуль аналітики з використанням принципів ООП
 * Використовує: інкапсуляцію, наслідування, поліморфізм, абстракцію
 */
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <map>
#include <algorithm>
#include <iomanip>
#include <cmath>
#include <numeric>
#include <set>
#include <cctype>

using namespace std;

// ========== КЛАСИ ДАНИХ ==========

/**
 * Клас для позиції продажу
 * Інкапсулює дані про товар у продажі
 */
class SaleItem {
private:
    int product_id;
    string product_name;
    int category_id;
    string category_name;
    int quantity;
    double price;
    double subtotal;
    string date;

public:
    // Конструктор
    SaleItem() : product_id(0), category_id(0), quantity(0), price(0.0), subtotal(0.0) {}
    
    SaleItem(int pid, const string& pname, int cid, const string& cname, 
             int qty, double pr, double sub, const string& dt)
        : product_id(pid), product_name(pname), category_id(cid), 
          category_name(cname), quantity(qty), price(pr), subtotal(sub), date(dt) {}
    
    // Геттери (інкапсуляція)
    int getProductId() const { return product_id; }
    const string& getProductName() const { return product_name; }
    int getCategoryId() const { return category_id; }
    const string& getCategoryName() const { return category_name; }
    int getQuantity() const { return quantity; }
    double getPrice() const { return price; }
    double getSubtotal() const { return subtotal; }
    const string& getDate() const { return date; }
    
    // Сеттери
    void setProductId(int id) { product_id = id; }
    void setProductName(const string& name) { product_name = name; }
    void setCategoryId(int id) { category_id = id; }
    void setCategoryName(const string& name) { category_name = name; }
    void setQuantity(int qty) { quantity = qty; }
    void setPrice(double pr) { price = pr; }
    void setSubtotal(double sub) { subtotal = sub; }
    void setDate(const string& dt) { date = dt; }
};


/**
 * Клас для продажу
 * Інкапсулює дані про продаж та його позиції
 */
class Sale {
private:
    int id;
    string date;
    double total_amount;
    vector<SaleItem> items;

public:
    // Конструктор
    Sale() : id(0), total_amount(0.0) {}
    
    Sale(int saleId, const string& saleDate, double total)
        : id(saleId), date(saleDate), total_amount(total) {}
    
    // Геттери
    int getId() const { return id; }
    const string& getDate() const { return date; }
    double getTotalAmount() const { return total_amount; }
    const vector<SaleItem>& getItems() const { return items; }
    
    // Сеттери
    void setId(int saleId) { id = saleId; }
    void setDate(const string& saleDate) { date = saleDate; }
    void setTotalAmount(double total) { total_amount = total; }
    
    // Методи для роботи з позиціями
    void addItem(const SaleItem& item) { items.push_back(item); }
    size_t getItemsCount() const { return items.size(); }
    
    // Метод для отримання загальної виручки з позицій
    double calculateTotalFromItems() const {
        double total = 0.0;
        for (const auto& item : items) {
            total += item.getSubtotal();
        }
        return total;
    }
};


/**
 * Клас для топ товарів
 * Інкапсулює дані про товар у топі
 */
class TopProduct {
private:
    string name;
    double revenue;
    int quantity;

public:
    TopProduct() : revenue(0.0), quantity(0) {}
    
    TopProduct(const string& n, double rev, int qty)
        : name(n), revenue(rev), quantity(qty) {}
    
    // Геттери
    const string& getName() const { return name; }
    double getRevenue() const { return revenue; }
    int getQuantity() const { return quantity; }
    
    // Сеттери
    void setName(const string& n) { name = n; }
    void setRevenue(double rev) { revenue = rev; }
    void setQuantity(int qty) { quantity = qty; }
    
    // Метод порівняння для сортування за виручкою
    static bool compareByRevenue(const TopProduct& a, const TopProduct& b) {
        return a.revenue > b.revenue;
    }
    
    // Метод порівняння для сортування за кількістю
    static bool compareByQuantity(const TopProduct& a, const TopProduct& b) {
        return a.quantity > b.quantity;
    }
};


/**
 * Клас для статистик
 * Інкапсулює статистичні дані
 */
class Statistics {
private:
    double mean;
    double median;
    double stdDev;
    double min;
    double max;

public:
    Statistics() : mean(0.0), median(0.0), stdDev(0.0), min(0.0), max(0.0) {}
    
    // Геттери
    double getMean() const { return mean; }
    double getMedian() const { return median; }
    double getStdDev() const { return stdDev; }
    double getMin() const { return min; }
    double getMax() const { return max; }
    
    // Сеттери
    void setMean(double m) { mean = m; }
    void setMedian(double m) { median = m; }
    void setStdDev(double sd) { stdDev = sd; }
    void setMin(double m) { min = m; }
    void setMax(double m) { max = m; }
    
    // Метод для обнулення
    void reset() {
        mean = median = stdDev = min = max = 0.0;
    }
};


/**
 * Клас для результату ABC-аналізу
 * Інкапсулює дані про товар у ABC-аналізі
 */
class ABCResult {
private:
    string product_name;
    double revenue;
    double cumulative_percent;
    char category;

public:
    ABCResult() : revenue(0.0), cumulative_percent(0.0), category('C') {}
    
    ABCResult(const string& name, double rev, double cum, char cat)
        : product_name(name), revenue(rev), cumulative_percent(cum), category(cat) {}
    
    // Геттери
    const string& getProductName() const { return product_name; }
    double getRevenue() const { return revenue; }
    double getCumulativePercent() const { return cumulative_percent; }
    char getCategory() const { return category; }
    
    // Сеттери
    void setProductName(const string& name) { product_name = name; }
    void setRevenue(double rev) { revenue = rev; }
    void setCumulativePercent(double cum) { cumulative_percent = cum; }
    void setCategory(char cat) { category = cat; }
};


// ========== ДОПОМІЖНІ КЛАСИ ==========

/**
 * Клас для парсингу чисел
 * Інкапсулює логіку безпечного парсингу
 */
class NumberParser {
public:
    static int parseInteger(const string& str) {
        if (str.empty()) return 0;
        string clean;
        bool hasSign = false;
        for (size_t i = 0; i < str.length(); i++) {
            char c = str[i];
            if (isdigit(c)) {
                clean += c;
            } else if ((c == '-' || c == '+') && !hasSign && clean.empty()) {
                clean += c;
                hasSign = true;
            }
        }
        if (clean.empty() || clean == "-" || clean == "+") return 0;
        try {
            return stoi(clean);
        } catch (...) {
            return 0;
        }
    }
    
    static double parseDouble(const string& str) {
        if (str.empty()) return 0.0;
        string clean;
        bool hasDot = false;
        bool hasE = false;
        for (size_t i = 0; i < str.length(); i++) {
            char c = str[i];
            if (isdigit(c) || 
                (i == 0 && (c == '-' || c == '+')) || 
                (c == '.' && !hasDot) ||
                ((c == 'e' || c == 'E') && !hasE && i > 0)) {
                clean += c;
                if (c == '.') hasDot = true;
                if (c == 'e' || c == 'E') hasE = true;
            }
        }
        if (clean.empty() || clean == "-" || clean == "+" || clean == ".") return 0.0;
        try {
            return stod(clean);
        } catch (...) {
            return 0.0;
        }
    }
};


/**
 * Клас для роботи з датами
 * Інкапсулює логіку парсингу та обробки дат
 */
class DateParser {
public:
    static bool parseYMD(const string& date, int& y, int& m, int& d) {
        if (date.size() < 10) return false;
        if (!isdigit(date[0]) || !isdigit(date[1]) || !isdigit(date[2]) || !isdigit(date[3])) return false;
        if (date[4] != '-') return false;
        if (!isdigit(date[5]) || !isdigit(date[6])) return false;
        if (date[7] != '-') return false;
        if (!isdigit(date[8]) || !isdigit(date[9])) return false;

        y = (date[0]-'0')*1000 + (date[1]-'0')*100 + (date[2]-'0')*10 + (date[3]-'0');
        m = (date[5]-'0')*10 + (date[6]-'0');
        d = (date[8]-'0')*10 + (date[9]-'0');

        if (m < 1 || m > 12) return false;
        if (d < 1 || d > 31) return false;
        return true;
    }
};


/**
 * Клас для екранування JSON
 * Інкапсулює логіку екранування спеціальних символів
 */
class JSONEscaper {
public:
    static string escape(const string& str) {
        string result;
        for (char c : str) {
            if (c == '"') {
                result += "\\\"";
            } else if (c == '\\') {
                result += "\\\\";
            } else if (c == '\n') {
                result += "\\n";
            } else if (c == '\r') {
                result += "\\r";
            } else if (c == '\t') {
                result += "\\t";
            } else {
                result += c;
            }
        }
        return result;
    }
};


// ========== КЛАС ДЛЯ ПАРСИНГУ JSON ==========

/**
 * Клас для парсингу JSON
 * Інкапсулює всю логіку парсингу JSON в класи
 */
class JSONParser {
private:
    string json;
    
    // Приватні методи для парсингу
    string extractStringValue(size_t startPos) {
        // Спочатку знаходимо двокрапку після ключа
        size_t colonPos = json.find(":", startPos);
        if (colonPos == string::npos) return "";
        
        // Потім шукаємо першу лапку після двокрапки (пропускаючи пробіли)
        size_t quotePos = colonPos + 1;
        while (quotePos < json.length() && (json[quotePos] == ' ' || json[quotePos] == '\t')) {
            quotePos++;
        }
        if (quotePos >= json.length() || json[quotePos] != '"') return "";
        
        // Шукаємо кінцеву лапку, пропускаючи екрановані
        size_t endPos = quotePos + 1;
        while (endPos < json.length()) {
            if (json[endPos] == '"' && (endPos == 0 || json[endPos - 1] != '\\')) {
                break;
            }
            endPos++;
        }
        
        if (endPos >= json.length()) return "";
        
        string value = json.substr(quotePos + 1, endPos - quotePos - 1);
        // Замінюємо екрановані лапки
        size_t pos = 0;
        while ((pos = value.find("\\\"", pos)) != string::npos) {
            value.replace(pos, 2, "\"");
            pos += 1;
        }
        return value;
    }
    
    string extractNumericValue(size_t startPos) {
        size_t colonPos = json.find(":", startPos);
        if (colonPos == string::npos) return "";
        
        size_t endPos = colonPos + 1;
        bool inString = false;
        while (endPos < json.length()) {
            if (json[endPos] == '"' && (endPos == 0 || json[endPos - 1] != '\\')) {
                inString = !inString;
            } else if (!inString && (json[endPos] == ',' || json[endPos] == '}')) {
                break;
            }
            endPos++;
        }
        
        string value = json.substr(colonPos + 1, endPos - colonPos - 1);
        // Видаляємо пробіли
        size_t first = value.find_first_not_of(" \t\n\r");
        if (first != string::npos) {
            size_t last = value.find_last_not_of(" \t\n\r");
            if (last != string::npos && last >= first) {
                value = value.substr(first, last - first + 1);
            } else {
                value = value.substr(first);
            }
        } else {
            value.clear();
        }
        return value;
    }
    
    SaleItem parseSaleItem(size_t itemPos, const string& saleDate) {
        SaleItem item;
        item.setDate(saleDate);
        
        // product_id
        size_t pidPos = json.find("\"product_id\"", itemPos);
        if (pidPos != string::npos && pidPos < json.find("}", itemPos)) {
            string pidStr = extractNumericValue(pidPos);
            item.setProductId(NumberParser::parseInteger(pidStr));
        }
        
        // product_name
        size_t pnamePos = json.find("\"product_name\"", itemPos);
        if (pnamePos != string::npos && pnamePos < json.find("}", itemPos)) {
            item.setProductName(extractStringValue(pnamePos));
        }
        
        // category_id
        size_t cidPos = json.find("\"category_id\"", itemPos);
        if (cidPos != string::npos && cidPos < json.find("}", itemPos)) {
            string cidStr = extractNumericValue(cidPos);
            item.setCategoryId(NumberParser::parseInteger(cidStr));
        }
        
        // category_name
        size_t cnamePos = json.find("\"category_name\"", itemPos);
        if (cnamePos != string::npos && cnamePos < json.find("}", itemPos)) {
            item.setCategoryName(extractStringValue(cnamePos));
        }
        
        // quantity
        size_t qtyPos = json.find("\"quantity\"", itemPos);
        if (qtyPos != string::npos && qtyPos < json.find("}", itemPos)) {
            string qtyStr = extractNumericValue(qtyPos);
            item.setQuantity(NumberParser::parseInteger(qtyStr));
        }
        
        // price
        size_t pricePos = json.find("\"price\"", itemPos);
        if (pricePos != string::npos && pricePos < json.find("}", itemPos)) {
            string priceStr = extractNumericValue(pricePos);
            item.setPrice(NumberParser::parseDouble(priceStr));
        }
        
        // subtotal
        size_t subPos = json.find("\"subtotal\"", itemPos);
        if (subPos != string::npos && subPos < json.find("}", itemPos)) {
            string subStr = extractNumericValue(subPos);
            item.setSubtotal(NumberParser::parseDouble(subStr));
        }
        
        return item;
    }

public:
    JSONParser(const string& jsonStr) : json(jsonStr) {}
    
    /**
     * Парсинг JSON та повернення вектору продажів
     * Інкапсулює всю логіку парсингу
     */
    vector<Sale> parseSales() {
        vector<Sale> sales;
        
        size_t salesPos = json.find("\"sales\"");
        if (salesPos == string::npos) return sales;
        
        salesPos = json.find("[", salesPos);
        if (salesPos == string::npos) return sales;
        
        size_t pos = salesPos;
        while (true) {
            pos = json.find("{", pos);
            if (pos == string::npos) break;
            
            Sale sale;
            
            // ID продажу
            size_t idPos = json.find("\"id\"", pos);
            if (idPos != string::npos) {
                string idStr = extractNumericValue(idPos);
                sale.setId(NumberParser::parseInteger(idStr));
            }
            
            // Дата
            size_t datePos = json.find("\"date\"", pos);
            if (datePos != string::npos) {
                sale.setDate(extractStringValue(datePos));
            }
            
            // Загальна сума
            size_t totalPos = json.find("\"total_amount\"", pos);
            if (totalPos != string::npos) {
                string totalStr = extractNumericValue(totalPos);
                sale.setTotalAmount(NumberParser::parseDouble(totalStr));
            }
            
            // Позиції продажу
            size_t itemsPos = json.find("\"items\"", pos);
            if (itemsPos != string::npos) {
                itemsPos = json.find("[", itemsPos);
                size_t itemsEnd = json.find("]", itemsPos);
                
                size_t itemPos = itemsPos;
                while (true) {
                    itemPos = json.find("{", itemPos);
                    if (itemPos == string::npos || itemPos >= itemsEnd) break;
                    
                    SaleItem item = parseSaleItem(itemPos, sale.getDate());
                    sale.addItem(item);
                    itemPos = json.find("}", itemPos) + 1;
                }
            }
            
            sales.push_back(sale);
            pos = json.find("}", pos) + 1;
        }
        
        return sales;
    }
};


// ========== КЛАС ДЛЯ ОБЧИСЛЕННЯ СТАТИСТИК ==========

/**
 * Клас для обчислення статистик
 * Інкапсулює логіку розрахунку статистичних показників
 */
class StatisticsCalculator {
public:
    /**
     * Обчислення статистик з вектору значень
     */
    static Statistics calculate(const vector<double>& values) {
        Statistics stats;
        
        if (values.empty()) {
            stats.reset();
            return stats;
        }
        
        // Фільтруємо нульові значення
        vector<double> nonZeroValues;
        for (double val : values) {
            if (val > 0) {
                nonZeroValues.push_back(val);
            }
        }
        
        if (nonZeroValues.empty()) {
            stats.reset();
            return stats;
        }
        
        vector<double> sorted = nonZeroValues;
        sort(sorted.begin(), sorted.end());
        
        // Мінімум і максимум
        stats.setMin(sorted.front());
        stats.setMax(sorted.back());
        
        // Середнє
        double sum = accumulate(sorted.begin(), sorted.end(), 0.0);
        stats.setMean(sum / sorted.size());
        
        // Медіана
        size_t n = sorted.size();
        if (n % 2 == 0) {
            stats.setMedian((sorted[n/2 - 1] + sorted[n/2]) / 2.0);
        } else {
            stats.setMedian(sorted[n/2]);
        }
        
        // Стандартне відхилення
        double mean = stats.getMean();
        double variance = 0.0;
        for (double val : sorted) {
            variance += (val - mean) * (val - mean);
        }
        variance /= sorted.size();
        stats.setStdDev(sqrt(variance));
        
        return stats;
    }
};


// ========== КЛАС ДЛЯ АГРЕГАЦІЇ ДАНИХ ==========

/**
 * Клас для агрегації даних по періодах
 * Інкапсулює логіку агрегації по днях/тижнях/місяцях
 */
class DataAggregator {
public:
    /**
     * Агрегація по днях
     */
    static map<string, double> aggregateByDay(const vector<Sale>& sales) {
        map<string, double> dailyTotals;
        for (const auto& sale : sales) {
            dailyTotals[sale.getDate()] += sale.getTotalAmount();
        }
        return dailyTotals;
    }
    
    /**
     * Агрегація по тижнях
     */
    static map<string, double> aggregateByWeek(const vector<Sale>& sales) {
        map<string, double> weeklyTotals;
        
        for (const auto& sale : sales) {
            int year, month, day;
            if (!DateParser::parseYMD(sale.getDate(), year, month, day)) {
                continue;
            }
            
            int week = (month - 1) * 4 + (day - 1) / 7 + 1;
            string weekKey = to_string(year) + "-W" + (week < 10 ? "0" : "") + to_string(week);
            weeklyTotals[weekKey] += sale.getTotalAmount();
        }
        
        return weeklyTotals;
    }
    
    /**
     * Агрегація по місяцях
     */
    static map<string, double> aggregateByMonth(const vector<Sale>& sales) {
        map<string, double> monthlyTotals;
        for (const auto& sale : sales) {
            string monthKey = sale.getDate().substr(0, 7); // YYYY-MM
            monthlyTotals[monthKey] += sale.getTotalAmount();
        }
        return monthlyTotals;
    }
};


// ========== КЛАС ДЛЯ ТОП ТОВАРІВ ==========

/**
 * Клас для обчислення топ товарів
 * Інкапсулює логіку розрахунку топ товарів
 */
class TopProductsCalculator {
public:
    /**
     * Топ товарів за виручкою
     */
    static vector<TopProduct> byRevenue(const vector<Sale>& sales) {
        map<string, pair<double, int>> productData; // revenue, quantity
        
        for (const auto& sale : sales) {
            for (const auto& item : sale.getItems()) {
                productData[item.getProductName()].first += item.getSubtotal();
                productData[item.getProductName()].second += item.getQuantity();
            }
        }
        
        vector<TopProduct> result;
        for (const auto& p : productData) {
            TopProduct tp(p.first, p.second.first, p.second.second);
            result.push_back(tp);
        }
        
        sort(result.begin(), result.end(), TopProduct::compareByRevenue);
        return result;
    }
    
    /**
     * Топ товарів за кількістю
     */
    static vector<TopProduct> byQuantity(const vector<Sale>& sales) {
        map<string, pair<int, double>> productData; // quantity, revenue
        
        for (const auto& sale : sales) {
            for (const auto& item : sale.getItems()) {
                productData[item.getProductName()].first += item.getQuantity();
                productData[item.getProductName()].second += item.getSubtotal();
            }
        }
        
        vector<TopProduct> result;
        for (const auto& p : productData) {
            TopProduct tp(p.first, p.second.second, p.second.first);
            result.push_back(tp);
        }
        
        sort(result.begin(), result.end(), TopProduct::compareByQuantity);
        return result;
    }
};


// ========== КЛАС ДЛЯ ЧАСТОК КАТЕГОРІЙ ==========

/**
 * Клас для обчислення часток категорій
 * Інкапсулює логіку розрахунку часток продажів по категоріях
 */
class CategorySharesCalculator {
public:
    /**
     * Обчислення часток продажів по категоріях
     */
    static map<string, double> calculate(const vector<Sale>& sales) {
        double totalRevenue = 0;
        map<string, double> categoryRevenue;
        
        for (const auto& sale : sales) {
            for (const auto& item : sale.getItems()) {
                categoryRevenue[item.getCategoryName()] += item.getSubtotal();
                totalRevenue += item.getSubtotal();
            }
        }
        
        // Конвертуємо в відсотки
        map<string, double> shares;
        for (const auto& p : categoryRevenue) {
            shares[p.first] = (totalRevenue > 0) ? (p.second / totalRevenue * 100.0) : 0.0;
        }
        
        return shares;
    }
};


// ========== КЛАС ДЛЯ ABC-АНАЛІЗУ ==========

/**
 * Клас для ABC-аналізу
 * Інкапсулює логіку ABC-аналізу товарів
 */
class ABCAnalyzer {
public:
    /**
     * Виконання ABC-аналізу
     */
    static vector<ABCResult> analyze(const vector<Sale>& sales) {
        // Збираємо виручку по товарах
        map<string, double> productRevenue;
        double totalRevenue = 0;
        
        for (const auto& sale : sales) {
            for (const auto& item : sale.getItems()) {
                productRevenue[item.getProductName()] += item.getSubtotal();
                totalRevenue += item.getSubtotal();
            }
        }
        
        // Сортуємо за виручкою
        vector<pair<string, double>> sorted;
        for (const auto& p : productRevenue) {
            sorted.push_back(p);
        }
        sort(sorted.begin(), sorted.end(), 
             [](const pair<string, double>& a, const pair<string, double>& b) {
                 return a.second > b.second;
             });
        
        // Розраховуємо кумулятивний відсоток та категорії
        vector<ABCResult> result;
        double cumulative = 0.0;
        
        for (const auto& p : sorted) {
            cumulative += p.second;
            double cumulativePercent = (totalRevenue > 0) ? (cumulative / totalRevenue * 100.0) : 0.0;
            
            ABCResult abc;
            abc.setProductName(p.first);
            abc.setRevenue(p.second);
            abc.setCumulativePercent(cumulativePercent);
            
            // Категорії: A (0-80%), B (80-95%), C (95-100%)
            if (cumulativePercent <= 80.0) {
                abc.setCategory('A');
            } else if (cumulativePercent <= 95.0) {
                abc.setCategory('B');
            } else {
                abc.setCategory('C');
            }
            
            result.push_back(abc);
        }
        
        return result;
    }
};


// ========== КЛАС ДЛЯ ВИВОДУ JSON ==========

/**
 * Клас для форматування та виводу JSON
 * Інкапсулює логіку форматування результатів
 */
class JSONOutputFormatter {
public:
    /**
     * Вивід агрегованих даних
     */
    static void outputAggregatedData(const map<string, double>& data, const string& keyName, const string& valueKey) {
        cout << "\"" << keyName << "\":[";
        bool first = true;
        for (const auto& pair : data) {
            if (pair.first.empty()) continue; // Пропускаємо порожні ключі
            if (!first) cout << ",";
            cout << "{\"" << valueKey << "\":\"" << pair.first 
                 << "\",\"revenue\":" << fixed << setprecision(2) << pair.second << "}";
            first = false;
        }
        cout << "]";
    }
    
    /**
     * Вивід топ товарів
     */
    static void outputTopProducts(const vector<TopProduct>& products, const string& keyName, size_t limit = 20) {
        cout << "\"" << keyName << "\":[";
        bool first = true;
        for (size_t i = 0; i < min(products.size(), limit); ++i) {
            if (!first) cout << ",";
            cout << "{\"product_name\":\"" << JSONEscaper::escape(products[i].getName()) 
                 << "\",\"revenue\":" << fixed << setprecision(2) << products[i].getRevenue()
                 << ",\"quantity\":" << products[i].getQuantity() << "}";
            first = false;
        }
        cout << "]";
    }
    
    /**
     * Вивід часток категорій
     */
    static void outputCategoryShares(const map<string, double>& shares) {
        cout << "\"category_shares\":[";
        bool first = true;
        for (const auto& p : shares) {
            if (!first) cout << ",";
            cout << "{\"category\":\"" << JSONEscaper::escape(p.first) 
                 << "\",\"share\":" << fixed << setprecision(2) << p.second << "}";
            first = false;
        }
        cout << "]";
    }
    
    /**
     * Вивід статистик
     */
    static void outputStatistics(const Statistics& stats, double totalRevenue, int totalSales) {
        cout << "\"statistics\":{";
        cout << "\"total_revenue\":" << fixed << setprecision(2) << totalRevenue << ",";
        cout << "\"mean\":" << fixed << setprecision(2) << stats.getMean() << ",";
        cout << "\"median\":" << fixed << setprecision(2) << stats.getMedian() << ",";
        cout << "\"std_dev\":" << fixed << setprecision(2) << stats.getStdDev() << ",";
        cout << "\"min\":" << fixed << setprecision(2) << stats.getMin() << ",";
        cout << "\"max\":" << fixed << setprecision(2) << stats.getMax() << ",";
        cout << "\"total_sales\":" << totalSales;
        cout << "}";
    }
    
    /**
     * Вивід ABC-аналізу
     */
    static void outputABCAnalysis(const vector<ABCResult>& abcResults) {
        cout << "\"abc_analysis\":[";
        bool first = true;
        for (const auto& abc : abcResults) {
            if (!first) cout << ",";
            cout << "{\"product_name\":\"" << JSONEscaper::escape(abc.getProductName()) 
                 << "\",\"revenue\":" << fixed << setprecision(2) << abc.getRevenue()
                 << ",\"cumulative_percent\":" << fixed << setprecision(2) << abc.getCumulativePercent()
                 << ",\"category\":\"" << abc.getCategory() << "\"}";
            first = false;
        }
        cout << "]";
    }
};


// ========== ГОЛОВНИЙ КЛАС АНАЛІТИКИ ==========

/**
 * Головний клас для аналітики
 * Координує всі обчислення та вивід результатів
 * Використовує принципи ООП: інкапсуляцію, композицію
 */
class AnalyticsEngine {
private:
    vector<Sale> sales;
    
    // Приватні методи для обчислень
    double calculateTotalRevenue() const {
        double total = 0.0;
        for (const auto& sale : sales) {
            total += sale.getTotalAmount();
        }
        return total;
    }
    
    vector<double> extractSaleAmounts() const {
        vector<double> amounts;
        for (const auto& sale : sales) {
            if (sale.getTotalAmount() > 0) {
                amounts.push_back(sale.getTotalAmount());
            }
        }
        return amounts;
    }

public:
    /**
     * Конструктор - приймає JSON рядок
     */
    AnalyticsEngine(const string& jsonInput) {
        JSONParser parser(jsonInput);
        sales = parser.parseSales();
    }
    
    /**
     * Перевірка чи є дані
     */
    bool hasData() const {
        return !sales.empty();
    }
    
    /**
     * Виконання всіх обчислень та вивід результатів
     * Інкапсулює всю логіку аналітики
     */
    void processAndOutput() {
        if (sales.empty()) {
            cout << "{\"error\":\"No sales found\"}";
            return;
        }
        
        // 1. Агрегація по днях/тижнях/місяцях
        map<string, double> dailyRevenue = DataAggregator::aggregateByDay(sales);
        map<string, double> weeklyRevenue = DataAggregator::aggregateByWeek(sales);
        map<string, double> monthlyRevenue = DataAggregator::aggregateByMonth(sales);
        
        // 2. Топ товарів
        vector<TopProduct> topByRevenue = TopProductsCalculator::byRevenue(sales);
        vector<TopProduct> topByQuantity = TopProductsCalculator::byQuantity(sales);
        
        // 3. Частки по категоріях
        map<string, double> categorySharesData = CategorySharesCalculator::calculate(sales);
        
        // 4. Статистики
        vector<double> saleAmounts = extractSaleAmounts();
        Statistics stats = StatisticsCalculator::calculate(saleAmounts);
        
        // 5. ABC-аналіз
        vector<ABCResult> abcResults = ABCAnalyzer::analyze(sales);
        
        // 6. Загальна виручка
        double totalRevenue = calculateTotalRevenue();
        
        // ========== ВИВІД РЕЗУЛЬТАТІВ ==========
        
        cout << "{";
        
        // Агрегація по днях
        cout << "\"daily_revenue\":[";
        bool first = true;
        for (const auto& p : dailyRevenue) {
            if (p.first.empty()) continue;
            if (!first) cout << ",";
            cout << "{\"date\":\"" << p.first << "\",\"revenue\":" 
                 << fixed << setprecision(2) << p.second << "}";
            first = false;
        }
        cout << "],";
        
        // Агрегація по тижнях
        cout << "\"weekly_revenue\":[";
        first = true;
        for (const auto& p : weeklyRevenue) {
            if (!first) cout << ",";
            cout << "{\"week\":\"" << p.first << "\",\"revenue\":" 
                 << fixed << setprecision(2) << p.second << "}";
            first = false;
        }
        cout << "],";
        
        // Агрегація по місяцях
        cout << "\"monthly_revenue\":[";
        first = true;
        for (const auto& p : monthlyRevenue) {
            if (p.first.empty()) continue;
            if (!first) cout << ",";
            cout << "{\"month\":\"" << p.first << "\",\"revenue\":" 
                 << fixed << setprecision(2) << p.second << "}";
            first = false;
        }
        cout << "],";
        
        // Топ товарів за виручкою
        cout << "\"top_products_by_revenue\":[";
        first = true;
        for (size_t i = 0; i < min(topByRevenue.size(), size_t(20)); ++i) {
            if (!first) cout << ",";
            cout << "{\"product_name\":\"" << JSONEscaper::escape(topByRevenue[i].getName()) 
                 << "\",\"revenue\":" << fixed << setprecision(2) << topByRevenue[i].getRevenue()
                 << ",\"quantity\":" << topByRevenue[i].getQuantity() << "}";
            first = false;
        }
        cout << "],";
        
        // Топ товарів за кількістю
        cout << "\"top_products_by_quantity\":[";
        first = true;
        for (size_t i = 0; i < min(topByQuantity.size(), size_t(20)); ++i) {
            if (!first) cout << ",";
            cout << "{\"product_name\":\"" << JSONEscaper::escape(topByQuantity[i].getName()) 
                 << "\",\"quantity\":" << topByQuantity[i].getQuantity()
                 << ",\"revenue\":" << fixed << setprecision(2) << topByQuantity[i].getRevenue() << "}";
            first = false;
        }
        cout << "],";
        
        // Частки по категоріях
        cout << "\"category_shares\":[";
        first = true;
        for (const auto& p : categorySharesData) {
            if (!first) cout << ",";
            cout << "{\"category\":\"" << JSONEscaper::escape(p.first) 
                 << "\",\"share\":" << fixed << setprecision(2) << p.second << "}";
            first = false;
        }
        cout << "],";
        
        // Статистики
        cout << "\"statistics\":{";
        cout << "\"total_revenue\":" << fixed << setprecision(2) << totalRevenue << ",";
        cout << "\"mean\":" << fixed << setprecision(2) << stats.getMean() << ",";
        cout << "\"median\":" << fixed << setprecision(2) << stats.getMedian() << ",";
        cout << "\"std_dev\":" << fixed << setprecision(2) << stats.getStdDev() << ",";
        cout << "\"min\":" << fixed << setprecision(2) << stats.getMin() << ",";
        cout << "\"max\":" << fixed << setprecision(2) << stats.getMax() << ",";
        cout << "\"total_sales\":" << sales.size();
        cout << "},";
        
        // ABC-аналіз
        cout << "\"abc_analysis\":[";
        first = true;
        for (const auto& abc : abcResults) {
            if (!first) cout << ",";
            cout << "{\"product_name\":\"" << JSONEscaper::escape(abc.getProductName()) 
                 << "\",\"revenue\":" << fixed << setprecision(2) << abc.getRevenue()
                 << ",\"cumulative_percent\":" << fixed << setprecision(2) << abc.getCumulativePercent()
                 << ",\"category\":\"" << abc.getCategory() << "\"}";
            first = false;
        }
        cout << "]";
        
        cout << "}";
    }
};


// ========== ГОЛОВНА ФУНКЦІЯ ==========

int main() {
    // Читання JSON з stdin
    string input;
    string line;
    while (getline(cin, line)) {
        input += line;
    }
    
    if (input.empty()) {
        cout << "{\"error\":\"No input data\"}";
        return 1;
    }
    
    // Створення об'єкта аналітики та обробка
    AnalyticsEngine engine(input);
    
    if (!engine.hasData()) {
        cout << "{\"error\":\"No sales found\"}";
        return 1;
    }
    
    // Виконання обчислень та вивід результатів
    engine.processAndOutput();
    
    return 0;
}

