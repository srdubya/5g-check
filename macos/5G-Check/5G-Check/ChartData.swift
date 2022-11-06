//
//  ChartData.swift
//  5G-Check
//
//  Created by Steve Wiley on 10/30/22.
//

import Foundation

class ChartData {
    var name: String
    var values: [String:Int]
    
    init(name: String) {
        self.name = name
        self.values = [:]
    }
    
    func incrementValue(withKey: String) {
        let present = self.values.contains { $0.key == withKey }
        if present {
            self.values.updateValue(self.values[withKey]! + 1, forKey: withKey)
        } else {
            self.values[withKey] = 1
        }
    }

    func clear() {
        self.values = [:]
    }
    
    static func example0() -> ChartData {
        let ret = ChartData(name: "rsrp")
        for _ in 1...1000 {
            ret.incrementValue(withKey: "-74")
            ret.incrementValue(withKey: "-78")
        }
        for _ in 1...500 {
            ret.incrementValue(withKey: "-76")
            ret.incrementValue(withKey: "-79")
        }
        for _ in 1...50 {
            ret.incrementValue(withKey: "-77")
            ret.incrementValue(withKey: "-1,024")
        }
        return ret
    }
    
    static func example1() -> ChartData {
        let ret = ChartData(name: "signal")
        for _ in 1...1000 {
            ret.incrementValue(withKey: "-72")
            ret.incrementValue(withKey: "-74")
            ret.incrementValue(withKey: "-78")
        }
        for _ in 1...500 {
            ret.incrementValue(withKey: "-76")
            ret.incrementValue(withKey: "-79")
        }
        for _ in 1...50 {
            ret.incrementValue(withKey: "-73")
            ret.incrementValue(withKey: "-77")
            ret.incrementValue(withKey: "-80")
            ret.incrementValue(withKey: "-1,024")
        }
        return ret
    }
}
