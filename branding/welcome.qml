import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 940
    height: 610
    minimumWidth: 760
    minimumHeight: 520
    visible: true
    title: "Welcome to Najs"
    color: "#07111C"

    component FeatureCard: Rectangle {
        property string heading
        property string body
        property string glyph

        Layout.fillWidth: true
        Layout.fillHeight: true
        radius: 18
        color: "#122536"
        border.color: "#23465D"
        border.width: 1

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 22
            spacing: 12

            Label {
                text: glyph
                color: "#59D2FF"
                font.pixelSize: 30
                font.bold: true
            }
            Label {
                text: heading
                color: "#F0F8FC"
                font.pixelSize: 18
                font.bold: true
            }
            Label {
                Layout.fillWidth: true
                Layout.fillHeight: true
                text: body
                color: "#A9C0CF"
                font.pixelSize: 14
                wrapMode: Text.WordWrap
                lineHeight: 1.18
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "transparent"
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#10283C" }
            GradientStop { position: 0.58; color: "#091722" }
            GradientStop { position: 1.0; color: "#050B12" }
        }
    }

    Rectangle {
        width: 430
        height: 430
        radius: 215
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.rightMargin: -180
        anchors.topMargin: -220
        color: "#185B78"
        opacity: 0.24
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 40
        spacing: 24

        RowLayout {
            Layout.fillWidth: true
            spacing: 22

            Image {
                source: "file:///usr/share/icons/hicolor/scalable/apps/najs.svg"
                sourceSize.width: 86
                sourceSize.height: 86
                Layout.preferredWidth: 86
                Layout.preferredHeight: 86
                fillMode: Image.PreserveAspectFit
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                Label {
                    text: "Welcome to Najs"
                    color: "#F4FAFD"
                    font.pixelSize: 32
                    font.bold: true
                }
                Label {
                    text: "A declarative Plasma desktop with explicit system generations."
                    color: "#8BE7FF"
                    font.pixelSize: 16
                }
            }

            Label {
                text: "0.1  DEVELOPMENT"
                color: "#7D9AAE"
                font.pixelSize: 12
                font.letterSpacing: 1.2
            }
        }

        GridLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            columns: width < 760 ? 1 : 3
            columnSpacing: 16
            rowSpacing: 16

            FeatureCard {
                heading: "Declare intent"
                glyph: "01"
                body: "Describe packages, services, profiles, and desktop policy in one strict TOML manifest."
            }
            FeatureCard {
                heading: "Inspect first"
                glyph: "02"
                body: "Use najs diff and najs doctor to understand the running system before changing it."
            }
            FeatureCard {
                heading: "Own the desktop"
                glyph: "03"
                body: "Najs Fold integrates Plasma, Konsole, SDDM, Fastfetch, and boot identity as one system."
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 14

            Label {
                Layout.fillWidth: true
                text: "Start with  najs doctor  in Konsole"
                color: "#8DA7B8"
                font.family: "Hack"
                font.pixelSize: 13
            }

            Button {
                text: "Documentation"
                onClicked: Qt.openUrlExternally("https://github.com/najs-os/najs")
            }

            Button {
                text: "Start using Najs"
                highlighted: true
                onClicked: window.close()
            }
        }
    }
}
