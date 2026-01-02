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

// Допоміжна функція для очищення рядка від нецифрових символів (для int)
int parseInteger(const string& str) {
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

// Допоміжна функція для очищення рядка від нецифрових символів (для double)
double parseDouble(const string& str) {
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

// Структури даних
struct SaleItem {
    int product_id;
    string product_name;
    int category_id;
    string category_name;
    int quantity;
    double price;
    double subtotal;
    string date;
};

struct Sale {
    int id;
    string date;
    double total_amount;
    vector<SaleItem> items;
};

// Парсинг JSON (спрощений, але достатній для структурованих даних)
vector<Sale> parseSales(const string& json) {
    vector<Sale> sales;
    
    // Шукаємо масив продажів
    size_t pos = json.find("\"sales\"");
    if (pos == string::npos) return sales;
    
    pos = json.find("[", pos);
    if (pos == string::npos) return sales;
    
    // Парсимо кожен продаж
    while (true) {
        pos = json.find("{", pos);
        if (pos == string::npos) break;
        
        Sale sale;
        
        // ID продажу
        size_t idPos = json.find("\"id\"", pos);
        if (idPos != string::npos && idPos < json.find("}", pos)) {
            idPos = json.find(":", idPos);
            if (idPos != string::npos) {
                // Шукаємо кому або закриваючу дужку, але не всередині рядка
                size_t idEnd = idPos + 1;
                bool inString = false;
                while (idEnd < json.length() && idEnd < json.find("}", pos)) {
                    if (json[idEnd] == '"' && (idEnd == 0 || json[idEnd - 1] != '\\')) {
                        inString = !inString;
                    } else if (!inString && (json[idEnd] == ',' || json[idEnd] == '}')) {
                        break;
                    }
                    idEnd++;
                }
                if (idEnd >= json.length()) idEnd = json.find("}", pos);
                string idStr = json.substr(idPos + 1, idEnd - idPos - 1);
                // Видаляємо пробіли
                size_t first = idStr.find_first_not_of(" \t\n\r");
                if (first != string::npos) {
                    size_t last = idStr.find_last_not_of(" \t\n\r");
                    if (last != string::npos && last >= first) {
                        idStr = idStr.substr(first, last - first + 1);
                    } else {
                        idStr = idStr.substr(first);
                    }
                } else {
                    idStr.clear();
                }
                sale.id = parseInteger(idStr);
            }
        }
        
        // Дата (прибрано перевірку datePos < json.find("}", pos) бо вона неправильна для вкладених JSON)
        size_t datePos = json.find("\"date\"", pos);
        if (datePos != string::npos) {
            datePos = json.find(":", datePos);
            datePos = json.find("\"", datePos);
            if (datePos != string::npos) {
                // Шукаємо кінцеву лапку, пропускаючи екрановані
                size_t dateEnd = datePos + 1;
                while (dateEnd < json.length()) {
                    if (json[dateEnd] == '"' && (dateEnd == 0 || json[dateEnd - 1] != '\\')) {
                        break;
                    }
                    dateEnd++;
                }
                if (dateEnd < json.length()) {
                    sale.date = json.substr(datePos + 1, dateEnd - datePos - 1);
                }
            }
        }
        
        // Загальна сума (прибрано перевірку totalPos < json.find("}", pos) бо вона неправильна для вкладених JSON)
        size_t totalPos = json.find("\"total_amount\"", pos);
        if (totalPos != string::npos) {
            totalPos = json.find(":", totalPos);
            if (totalPos != string::npos) {
                // Шукаємо кому або закриваючу дужку, але не всередині рядка
                size_t totalEnd = totalPos + 1;
                bool inString = false;
                while (totalEnd < json.length() && totalEnd < json.find("}", pos)) {
                    if (json[totalEnd] == '"' && (totalEnd == 0 || json[totalEnd - 1] != '\\')) {
                        inString = !inString;
                    } else if (!inString && (json[totalEnd] == ',' || json[totalEnd] == '}')) {
                        break;
                    }
                    totalEnd++;
                }
                if (totalEnd >= json.length()) totalEnd = json.find("}", pos);
                string totalStr = json.substr(totalPos + 1, totalEnd - totalPos - 1);
                // Видаляємо пробіли
                size_t first = totalStr.find_first_not_of(" \t\n\r");
                if (first != string::npos) {
                    size_t last = totalStr.find_last_not_of(" \t\n\r");
                    if (last != string::npos && last >= first) {
                        totalStr = totalStr.substr(first, last - first + 1);
                    } else {
                        totalStr = totalStr.substr(first);
                    }
                } else {
                    totalStr.clear();
                }
                sale.total_amount = parseDouble(totalStr);
            }
        }
        
        // Позиції продажу (прибрано перевірку itemsPos < json.find("}", pos) бо вона неправильна для вкладених JSON)
        size_t itemsPos = json.find("\"items\"", pos);
        if (itemsPos != string::npos) {
            itemsPos = json.find("[", itemsPos);
            size_t itemsEnd = json.find("]", itemsPos);
            
            size_t itemPos = itemsPos;
            while (true) {
                itemPos = json.find("{", itemPos);
                if (itemPos == string::npos || itemPos >= itemsEnd) break;
                
                SaleItem item;
                
                // product_id
                size_t pidPos = json.find("\"product_id\"", itemPos);
                if (pidPos != string::npos && pidPos < json.find("}", itemPos)) {
                    pidPos = json.find(":", pidPos);
                    if (pidPos != string::npos) {
                        // Шукаємо кому або закриваючу дужку, але не всередині рядка
                        size_t pidEnd = pidPos + 1;
                        bool inString = false;
                        while (pidEnd < json.length() && pidEnd < json.find("}", itemPos)) {
                            if (json[pidEnd] == '"' && (pidEnd == 0 || json[pidEnd - 1] != '\\')) {
                                inString = !inString;
                            } else if (!inString && (json[pidEnd] == ',' || json[pidEnd] == '}')) {
                                break;
                            }
                            pidEnd++;
                        }
                        if (pidEnd >= json.length()) pidEnd = json.find("}", itemPos);
                        string pidStr = json.substr(pidPos + 1, pidEnd - pidPos - 1);
                        size_t first = pidStr.find_first_not_of(" \t\n\r");
                        if (first != string::npos) {
                            size_t last = pidStr.find_last_not_of(" \t\n\r");
                            if (last != string::npos && last >= first) {
                                pidStr = pidStr.substr(first, last - first + 1);
                            } else {
                                pidStr = pidStr.substr(first);
                            }
                        } else {
                            pidStr.clear();
                        }
                        item.product_id = parseInteger(pidStr);
                    }
                }
                
                // product_name
                size_t pnamePos = json.find("\"product_name\"", itemPos);
                if (pnamePos != string::npos && pnamePos < json.find("}", itemPos)) {
                    pnamePos = json.find(":", pnamePos);
                    pnamePos = json.find("\"", pnamePos);
                    if (pnamePos != string::npos) {
                        // Шукаємо кінцеву лапку, пропускаючи екрановані
                        size_t pnameEnd = pnamePos + 1;
                        while (pnameEnd < json.length()) {
                            if (json[pnameEnd] == '"' && (pnameEnd == 0 || json[pnameEnd - 1] != '\\')) {
                                break;
                            }
                            pnameEnd++;
                        }
                        if (pnameEnd < json.length()) {
                            string name = json.substr(pnamePos + 1, pnameEnd - pnamePos - 1);
                            // Замінюємо екрановані лапки на звичайні
                            size_t pos = 0;
                            while ((pos = name.find("\\\"", pos)) != string::npos) {
                                name.replace(pos, 2, "\"");
                                pos += 1;
                            }
                            item.product_name = name;
                        }
                    }
                }
                
                // category_id
                size_t cidPos = json.find("\"category_id\"", itemPos);
                if (cidPos != string::npos && cidPos < json.find("}", itemPos)) {
                    cidPos = json.find(":", cidPos);
                    if (cidPos != string::npos) {
                        // Шукаємо кому або закриваючу дужку, але не всередині рядка
                        size_t cidEnd = cidPos + 1;
                        bool inString = false;
                        while (cidEnd < json.length() && cidEnd < json.find("}", itemPos)) {
                            if (json[cidEnd] == '"' && (cidEnd == 0 || json[cidEnd - 1] != '\\')) {
                                inString = !inString;
                            } else if (!inString && (json[cidEnd] == ',' || json[cidEnd] == '}')) {
                                break;
                            }
                            cidEnd++;
                        }
                        if (cidEnd >= json.length()) cidEnd = json.find("}", itemPos);
                        string cidStr = json.substr(cidPos + 1, cidEnd - cidPos - 1);
                        size_t first = cidStr.find_first_not_of(" \t\n\r");
                        if (first != string::npos) {
                            size_t last = cidStr.find_last_not_of(" \t\n\r");
                            if (last != string::npos && last >= first) {
                                cidStr = cidStr.substr(first, last - first + 1);
                            } else {
                                cidStr = cidStr.substr(first);
                            }
                        } else {
                            cidStr.clear();
                        }
                        item.category_id = parseInteger(cidStr);
                    }
                }
                
                // category_name
                size_t cnamePos = json.find("\"category_name\"", itemPos);
                if (cnamePos != string::npos && cnamePos < json.find("}", itemPos)) {
                    cnamePos = json.find(":", cnamePos);
                    cnamePos = json.find("\"", cnamePos);
                    if (cnamePos != string::npos) {
                        // Шукаємо кінцеву лапку, пропускаючи екрановані
                        size_t cnameEnd = cnamePos + 1;
                        while (cnameEnd < json.length()) {
                            if (json[cnameEnd] == '"' && (cnameEnd == 0 || json[cnameEnd - 1] != '\\')) {
                                break;
                            }
                            cnameEnd++;
                        }
                        if (cnameEnd < json.length()) {
                            string name = json.substr(cnamePos + 1, cnameEnd - cnamePos - 1);
                            // Замінюємо екрановані лапки на звичайні
                            size_t pos = 0;
                            while ((pos = name.find("\\\"", pos)) != string::npos) {
                                name.replace(pos, 2, "\"");
                                pos += 1;
                            }
                            item.category_name = name;
                        }
                    }
                }
                
                // quantity
                size_t qtyPos = json.find("\"quantity\"", itemPos);
                if (qtyPos != string::npos && qtyPos < json.find("}", itemPos)) {
                    qtyPos = json.find(":", qtyPos);
                    if (qtyPos != string::npos) {
                        // Шукаємо кому або закриваючу дужку, але не всередині рядка
                        size_t qtyEnd = qtyPos + 1;
                        bool inString = false;
                        while (qtyEnd < json.length() && qtyEnd < json.find("}", itemPos)) {
                            if (json[qtyEnd] == '"' && (qtyEnd == 0 || json[qtyEnd - 1] != '\\')) {
                                inString = !inString;
                            } else if (!inString && (json[qtyEnd] == ',' || json[qtyEnd] == '}')) {
                                break;
                            }
                            qtyEnd++;
                        }
                        if (qtyEnd >= json.length()) qtyEnd = json.find("}", itemPos);
                        string qtyStr = json.substr(qtyPos + 1, qtyEnd - qtyPos - 1);
                        size_t first = qtyStr.find_first_not_of(" \t\n\r");
                        if (first != string::npos) {
                            size_t last = qtyStr.find_last_not_of(" \t\n\r");
                            if (last != string::npos && last >= first) {
                                qtyStr = qtyStr.substr(first, last - first + 1);
                            } else {
                                qtyStr = qtyStr.substr(first);
                            }
                        } else {
                            qtyStr.clear();
                        }
                        item.quantity = parseInteger(qtyStr);
                    }
                }
                
                // price
                size_t pricePos = json.find("\"price\"", itemPos);
                if (pricePos != string::npos && pricePos < json.find("}", itemPos)) {
                    pricePos = json.find(":", pricePos);
                    if (pricePos != string::npos) {
                        // Шукаємо кому або закриваючу дужку, але не всередині рядка
                        size_t priceEnd = pricePos + 1;
                        bool inString = false;
                        while (priceEnd < json.length() && priceEnd < json.find("}", itemPos)) {
                            if (json[priceEnd] == '"' && (priceEnd == 0 || json[priceEnd - 1] != '\\')) {
                                inString = !inString;
                            } else if (!inString && (json[priceEnd] == ',' || json[priceEnd] == '}')) {
                                break;
                            }
                            priceEnd++;
                        }
                        if (priceEnd >= json.length()) priceEnd = json.find("}", itemPos);
                        string priceStr = json.substr(pricePos + 1, priceEnd - pricePos - 1);
                        size_t first = priceStr.find_first_not_of(" \t\n\r");
                        if (first != string::npos) {
                            size_t last = priceStr.find_last_not_of(" \t\n\r");
                            if (last != string::npos && last >= first) {
                                priceStr = priceStr.substr(first, last - first + 1);
                            } else {
                                priceStr = priceStr.substr(first);
                            }
                        } else {
                            priceStr.clear();
                        }
                        item.price = parseDouble(priceStr);
                    }
                }
                
                // subtotal
                size_t subPos = json.find("\"subtotal\"", itemPos);
                if (subPos != string::npos && subPos < json.find("}", itemPos)) {
                    subPos = json.find(":", subPos);
                    if (subPos != string::npos) {
                        // Шукаємо кому або закриваючу дужку, але не всередині рядка
                        size_t subEnd = subPos + 1;
                        bool inString = false;
                        while (subEnd < json.length() && subEnd < json.find("}", itemPos)) {
                            if (json[subEnd] == '"' && (subEnd == 0 || json[subEnd - 1] != '\\')) {
                                inString = !inString;
                            } else if (!inString && (json[subEnd] == ',' || json[subEnd] == '}')) {
                                break;
                            }
                            subEnd++;
                        }
                        if (subEnd >= json.length()) subEnd = json.find("}", itemPos);
                        string subStr = json.substr(subPos + 1, subEnd - subPos - 1);
                        size_t first = subStr.find_first_not_of(" \t\n\r");
                        if (first != string::npos) {
                            size_t last = subStr.find_last_not_of(" \t\n\r");
                            if (last != string::npos && last >= first) {
                                subStr = subStr.substr(first, last - first + 1);
                            } else {
                                subStr = subStr.substr(first);
                            }
                        } else {
                            subStr.clear();
                        }
                        item.subtotal = parseDouble(subStr);
                    }
                }
                
                // date (з продажу)
                item.date = sale.date;
                
                sale.items.push_back(item);
                itemPos = json.find("}", itemPos) + 1;
            }
        }
        
        sales.push_back(sale);
        pos = json.find("}", pos) + 1;
    }
    
    return sales;
}

// Агрегація продажів по днях
map<string, double> aggregateByDay(const vector<Sale>& sales) {
    map<string, double> dailyTotals;
    for (const auto& sale : sales) {
        dailyTotals[sale.date] += sale.total_amount;
    }
    return dailyTotals;
}

// Екранування рядка для JSON
static string escapeJSON(const string& str) {
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

// Безпечний парсинг дати без stoi
static bool parseYMD(const string& date, int& y, int& m, int& d) {
    // допускаємо YYYY-MM-DD або YYYY-MM-DDTHH:MM:SS...
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

// Агрегація продажів по тижнях
map<string, double> aggregateByWeek(const vector<Sale>& sales) {
    map<string, double> weeklyTotals;

    for (const auto& sale : sales) {
        int year, month, day;
        if (!parseYMD(sale.date, year, month, day)) {
            // якщо дата крива — просто пропускаємо, щоб не падало
            continue;
        }

        // простий "тиждень" як ти й робив
        int week = (month - 1) * 4 + (day - 1) / 7 + 1;
        string weekKey = to_string(year) + "-W" + (week < 10 ? "0" : "") + to_string(week);
        weeklyTotals[weekKey] += sale.total_amount;
    }

    return weeklyTotals;
}

// Агрегація продажів по місяцях
map<string, double> aggregateByMonth(const vector<Sale>& sales) {
    map<string, double> monthlyTotals;
    for (const auto& sale : sales) {
        string monthKey = sale.date.substr(0, 7); // YYYY-MM
        monthlyTotals[monthKey] += sale.total_amount;
    }
    return monthlyTotals;
}

// Топ товарів за виручкою
// Структура для топ товарів (назва, виручка, кількість)
struct TopProduct {
    string name;
    double revenue;
    int quantity;
};

vector<TopProduct> topProductsByRevenue(const vector<Sale>& sales) {
    map<string, pair<double, int>> productData; // revenue, quantity
    for (const auto& sale : sales) {
        for (const auto& item : sale.items) {
            productData[item.product_name].first += item.subtotal;
            productData[item.product_name].second += item.quantity;
        }
    }
    
    vector<TopProduct> result;
    for (const auto& p : productData) {
        TopProduct tp;
        tp.name = p.first;
        tp.revenue = p.second.first;
        tp.quantity = p.second.second;
        result.push_back(tp);
    }
    
    sort(result.begin(), result.end(), 
         [](const TopProduct& a, const TopProduct& b) {
             return a.revenue > b.revenue;
         });
    
    return result;
}

// Топ товарів за кількістю (також з виручкою)
vector<TopProduct> topProductsByQuantity(const vector<Sale>& sales) {
    map<string, pair<int, double>> productData; // quantity, revenue
    for (const auto& sale : sales) {
        for (const auto& item : sale.items) {
            productData[item.product_name].first += item.quantity;
            productData[item.product_name].second += item.subtotal;
        }
    }
    
    vector<TopProduct> result;
    for (const auto& p : productData) {
        TopProduct tp;
        tp.name = p.first;
        tp.quantity = p.second.first;
        tp.revenue = p.second.second;
        result.push_back(tp);
    }
    
    sort(result.begin(), result.end(), 
         [](const TopProduct& a, const TopProduct& b) {
             return a.quantity > b.quantity;
         });
    
    return result;
}

// Частки продажів по категоріях
map<string, double> categoryShares(const vector<Sale>& sales) {
    double totalRevenue = 0;
    map<string, double> categoryRevenue;
    
    for (const auto& sale : sales) {
        for (const auto& item : sale.items) {
            categoryRevenue[item.category_name] += item.subtotal;
            totalRevenue += item.subtotal;
        }
    }
    
    // Конвертуємо в відсотки
    map<string, double> shares;
    for (const auto& p : categoryRevenue) {
        shares[p.first] = (totalRevenue > 0) ? (p.second / totalRevenue * 100.0) : 0.0;
    }
    
    return shares;
}

// Статистики: середнє, медіана, стандартне відхилення
struct Statistics {
    double mean;
    double median;
    double stdDev;
    double min;
    double max;
};

Statistics calculateStatistics(const vector<double>& values) {
    Statistics stats;
    
    if (values.empty()) {
        stats.mean = stats.median = stats.stdDev = stats.min = stats.max = 0.0;
        return stats;
    }
    
    vector<double> sorted = values;
    sort(sorted.begin(), sorted.end());
    
    // Мінімум і максимум
    stats.min = sorted.front();
    stats.max = sorted.back();
    
    // Середнє
    stats.mean = accumulate(sorted.begin(), sorted.end(), 0.0) / sorted.size();
    
    // Медіана
    size_t n = sorted.size();
    if (n % 2 == 0) {
        stats.median = (sorted[n/2 - 1] + sorted[n/2]) / 2.0;
    } else {
        stats.median = sorted[n/2];
    }
    
    // Стандартне відхилення
    double variance = 0.0;
    for (double val : sorted) {
        variance += (val - stats.mean) * (val - stats.mean);
    }
    variance /= sorted.size();
    stats.stdDev = sqrt(variance);
    
    return stats;
}

// ABC-аналіз
struct ABCResult {
    string product_name;
    double revenue;
    double cumulative_percent;
    char category; // A, B, або C
};

vector<ABCResult> abcAnalysis(const vector<Sale>& sales) {
    // Збираємо виручку по товарах
    map<string, double> productRevenue;
    double totalRevenue = 0;
    
    for (const auto& sale : sales) {
        for (const auto& item : sale.items) {
            productRevenue[item.product_name] += item.subtotal;
            totalRevenue += item.subtotal;
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
        abc.product_name = p.first;
        abc.revenue = p.second;
        abc.cumulative_percent = cumulativePercent;
        
        // Категорії: A (0-80%), B (80-95%), C (95-100%)
        if (cumulativePercent <= 80.0) {
            abc.category = 'A';
        } else if (cumulativePercent <= 95.0) {
            abc.category = 'B';
        } else {
            abc.category = 'C';
        }
        
        result.push_back(abc);
    }
    
    return result;
}

// Вивід JSON
void outputJSON(const map<string, double>& data, const string& keyName) {
    cout << "\"" << keyName << "\":[";
    bool first = true;
    for (const auto& pair : data) {
        if (!first) cout << ",";
        cout << "{\"key\":\"" << pair.first << "\",\"value\":" << fixed << setprecision(2) << pair.second << "}";
        first = false;
    }
    cout << "]";
}

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
    
    // Парсинг продажів
    vector<Sale> sales = parseSales(input);
    
    if (sales.empty()) {
        cout << "{\"error\":\"No sales found\"}";
        return 1;
    }
    
    // ========== ОБЧИСЛЕННЯ АНАЛІТИКИ ==========
    
    // 1. Агрегація по днях/тижнях/місяцях
    map<string, double> dailyRevenue = aggregateByDay(sales);
    map<string, double> weeklyRevenue = aggregateByWeek(sales);
    map<string, double> monthlyRevenue = aggregateByMonth(sales);
    
    // 2. Топ товарів
    vector<TopProduct> topByRevenue = topProductsByRevenue(sales);
    vector<TopProduct> topByQuantity = topProductsByQuantity(sales);
    
    // 3. Частки по категоріях
    map<string, double> categorySharesData = categoryShares(sales);
    
    // 4. Статистики (середній чек, медіана, std dev)
    // Фільтруємо нульові значення для коректного розрахунку мінімуму
    vector<double> saleAmounts;
    for (const auto& sale : sales) {
        if (sale.total_amount > 0) {  // Пропускаємо нульові продажі
            saleAmounts.push_back(sale.total_amount);
        }
    }
    Statistics stats = calculateStatistics(saleAmounts);
    
    // 5. ABC-аналіз
    vector<ABCResult> abcResults = abcAnalysis(sales);
    
    // ========== ВИВІД РЕЗУЛЬТАТІВ ==========
    
    cout << "{";
    
    // Агрегація по днях
    cout << "\"daily_revenue\":[";
    bool first = true;
    for (const auto& p : dailyRevenue) {
        if (p.first.empty()) continue; // Пропускаємо порожні дати
        if (!first) cout << ",";
        cout << "{\"date\":\"" << p.first << "\",\"revenue\":" << fixed << setprecision(2) << p.second << "}";
        first = false;
    }
    cout << "],";
    
    // Агрегація по тижнях
    cout << "\"weekly_revenue\":[";
    first = true;
    for (const auto& p : weeklyRevenue) {
        if (!first) cout << ",";
        cout << "{\"week\":\"" << p.first << "\",\"revenue\":" << fixed << setprecision(2) << p.second << "}";
        first = false;
    }
    cout << "],";
    
    // Агрегація по місяцях
    cout << "\"monthly_revenue\":[";
    first = true;
    for (const auto& p : monthlyRevenue) {
        if (p.first.empty()) continue; // Пропускаємо порожні місяці
        if (!first) cout << ",";
        cout << "{\"month\":\"" << p.first << "\",\"revenue\":" << fixed << setprecision(2) << p.second << "}";
        first = false;
    }
    cout << "],";
    
    // Топ товарів за виручкою
    cout << "\"top_products_by_revenue\":[";
    first = true;
    for (size_t i = 0; i < min(topByRevenue.size(), size_t(20)); ++i) {
        if (!first) cout << ",";
        cout << "{\"product_name\":\"" << escapeJSON(topByRevenue[i].name) 
             << "\",\"revenue\":" << fixed << setprecision(2) << topByRevenue[i].revenue
             << ",\"quantity\":" << topByRevenue[i].quantity << "}";
        first = false;
    }
    cout << "],";
    
    // Топ товарів за кількістю
    cout << "\"top_products_by_quantity\":[";
    first = true;
    for (size_t i = 0; i < min(topByQuantity.size(), size_t(20)); ++i) {
        if (!first) cout << ",";
        cout << "{\"product_name\":\"" << escapeJSON(topByQuantity[i].name) 
             << "\",\"quantity\":" << topByQuantity[i].quantity
             << ",\"revenue\":" << fixed << setprecision(2) << topByQuantity[i].revenue << "}";
        first = false;
    }
    cout << "],";
    
    // Частки по категоріях
    cout << "\"category_shares\":[";
    first = true;
    for (const auto& p : categorySharesData) {
        if (!first) cout << ",";
        cout << "{\"category\":\"" << escapeJSON(p.first) 
             << "\",\"share\":" << fixed << setprecision(2) << p.second << "}";
        first = false;
    }
    cout << "],";
    
    // Загальна виручка
    double total_revenue = 0;
    for (const auto& sale : sales) {
        total_revenue += sale.total_amount;
    }
    
    // Статистики
    cout << "\"statistics\":{";
    cout << "\"total_revenue\":" << fixed << setprecision(2) << total_revenue << ",";
    cout << "\"mean\":" << fixed << setprecision(2) << stats.mean << ",";
    cout << "\"median\":" << fixed << setprecision(2) << stats.median << ",";
    cout << "\"std_dev\":" << fixed << setprecision(2) << stats.stdDev << ",";
    cout << "\"min\":" << fixed << setprecision(2) << stats.min << ",";
    cout << "\"max\":" << fixed << setprecision(2) << stats.max << ",";
    cout << "\"total_sales\":" << sales.size();
    cout << "},";
    
    // ABC-аналіз
    cout << "\"abc_analysis\":[";
    first = true;
    for (const auto& abc : abcResults) {
        if (!first) cout << ",";
        cout << "{\"product_name\":\"" << escapeJSON(abc.product_name) 
             << "\",\"revenue\":" << fixed << setprecision(2) << abc.revenue
             << ",\"cumulative_percent\":" << fixed << setprecision(2) << abc.cumulative_percent
             << ",\"category\":\"" << abc.category << "\"}";
        first = false;
    }
    cout << "]";
    
    cout << "}";
    
    return 0;
}
