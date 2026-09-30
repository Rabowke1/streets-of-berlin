#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include <initializer_list>
#include "BrawlerPlayerController.generated.h"

class ABrawlerGameMode;

/**
 * Fragt Tastatur und Gamepad direkt ab und leitet die Eingaben an die Spielfigur bzw. das Menue weiter.
 * Die Belegung kommt aus UBrawlerSettings (im Optionsmenue aenderbar).
 *
 *  Standard Tastatur: WASD/Pfeile = Laufen, J = Schlag, K/Leertaste = Sprung, L = Spezial, I = Rueckschlag,
 *                     Enter/P = Start/Pause, Esc = Pause/Zurueck
 *  Standard Gamepad:  Stick/D-Pad, X = Schlag, A = Sprung, Y = Spezial, B = Rueckschlag, Start = Start/Pause
 *  Menues:            Pfeile/D-Pad/Stick, Enter/A = OK, Esc/B = Zurueck (unabhaengig von der Belegung)
 */
UCLASS()
class STREETSOFBERLIN_API ABrawlerPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	ABrawlerPlayerController();

	virtual void BeginPlay() override;
	virtual void PlayerTick(float DeltaTime) override;

private:
	void TickMenu(ABrawlerGameMode* GM);
	void TickRebind(ABrawlerGameMode* GM);
	bool AnyJustPressed(std::initializer_list<FKey> Keys) const;

	/** Stick-Richtung des letzten Frames (fuer Menue-Navigation per Stick) */
	FIntPoint PrevStickDir = FIntPoint::ZeroValue;
	/** Alle digitalen Tasten (fuer das Neubelegen) */
	TArray<FKey> BindableKeys;
};
