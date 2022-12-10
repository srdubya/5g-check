//
//  _G_CheckApp.swift
//  5G-Check
//
//  Created by Steve Wiley on 10/29/22.
//

import SwiftUI

@main
struct CheckApp: App {
    @StateObject var gatewayState = GatewayState(asPreview: false)

    let timer = Timer.publish(every: 5, on: .main, in: .common).autoconnect()
    
    var body: some Scene {
        WindowGroup("Internet Gateway Statistics", id: "StatisticsWindow") {
            ContentView()
                .frame(minWidth: 300, idealWidth: 400, minHeight: 200, idealHeight: 300)
                .environmentObject(gatewayState)
                .navigationTitle("Internet GatewayStatistics \(gatewayState.elapsed)")
                .onDisappear(perform: {
                    gatewayState.isShowingStatistics = false
                })
        }
        .handlesExternalEvents(matching: ["StatisticsWindow"])

        MenuBarExtra(content: {
            Button("Statistics...") {
                gatewayState.isShowingStatistics = true
                OpenWindows.MainWindow.open()
            }.disabled(gatewayState.isShowingStatistics)
            Button("Quit") {
                NSApplication.shared.terminate(nil)
            }
        }, label: {
            Text(gatewayState.state).onReceive(timer, perform: { _ in
                gatewayState.update()
            })
        })
    }
}

enum OpenWindows: String, CaseIterable {
    case MainWindow = "StatisticsWindow"

    func open() {
        if let url = URL(string: "StatisticsWindow://\(rawValue)") {
            NSWorkspace.shared.open(url)
        }
    }
}
